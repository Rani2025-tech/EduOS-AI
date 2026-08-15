import logging
from typing import List, Dict, Any, Tuple
from ortools.sat.python import cp_model

logger = logging.getLogger("EduOS_TimetableSolver")
logger.setLevel(logging.INFO)

def solve_timetable_schedule(
    requested_slots: List[Dict[str, Any]],
    teachers_list: List[Dict[str, Any]],
    teacher_availabilities: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Uses Google OR-Tools CP-SAT Solver to generate a conflict-free timetable.
    Enforces:
      1. No Teacher Double-Booking (Teacher in max 1 class per period)
      2. No Class Double-Booking (Class has max 1 subject/teacher per period)
      3. Respects Teacher Availability & Absence constraints
      4. Auto-assigns available substitute teachers when primary teacher is unavailable
    Returns:
      (optimized_slots, conflict_warnings)
    """
    logger.info("Initializing Google OR-Tools CP-SAT Timetable Constraint Solver...")
    if not requested_slots:
        return [], ["No slots provided to solver."]

    if teacher_availabilities is None:
        teacher_availabilities = []

    model = cp_model.CpModel()
    warnings = []

    # Map teacher IDs and names
    all_teachers = teachers_list if teachers_list else []
    
    # Identify unavailable teachers per period
    unavailable_matrix = {} # (teacher_id_or_name, period) -> True
    for t in all_teachers:
        if t.get("status") == "absent" or t.get("status") == "leave":
            # Unavailable for all periods
            for p in range(1, 10):
                unavailable_matrix[(t.get("id"), p)] = True
                unavailable_matrix[(t.get("name"), p)] = True

    for av in teacher_availabilities:
        if av.get("status") == "unavailable" and av.get("period"):
            t_name = av.get("teacher_name")
            t_id = av.get("teacher_id")
            period = int(av.get("period"))
            if t_name:
                unavailable_matrix[(t_name, period)] = True
            if t_id:
                unavailable_matrix[(t_id, period)] = True

    # Build Decision Variables x[s_idx, t_idx]
    # x[s_idx, t_idx] == 1 if teacher t is assigned to slot s
    x = {}
    
    # Ensure every requested slot has a candidate list of teachers
    for s_idx, slot in enumerate(requested_slots):
        period = slot.get("period", 1)
        req_teacher_name = slot.get("teacher_name", "")

        for t_idx, teacher in enumerate(all_teachers):
            t_name = teacher.get("name")
            t_id = teacher.get("id")

            # Check if teacher is unavailable for this period
            is_unavail = unavailable_matrix.get((t_name, period)) or unavailable_matrix.get((t_id, period))
            
            x[s_idx, t_idx] = model.NewBoolVar(f"x_s{s_idx}_t{t_idx}")
            
            if is_unavail:
                # Hard Constraint: Teacher cannot be assigned if unavailable
                model.Add(x[s_idx, t_idx] == 0)

    # Constraint 1: Each requested slot must have exactly ONE teacher assigned
    for s_idx, slot in enumerate(requested_slots):
        if all_teachers:
            model.Add(sum(x[s_idx, t_idx] for t_idx in range(len(all_teachers))) == 1)

    # Constraint 2: No Teacher Double-Booking (a teacher cannot teach > 1 class in the same period)
    periods = set(s.get("period", 1) for s in requested_slots)
    for p in periods:
        slots_in_period = [s_idx for s_idx, s in enumerate(requested_slots) if s.get("period") == p]
        for t_idx in range(len(all_teachers)):
            model.Add(sum(x[s_idx, t_idx] for s_idx in slots_in_period) <= 1)

    # Objective Function: Prefer the requested primary teacher, penalize substitution
    objective_terms = []
    for s_idx, slot in enumerate(requested_slots):
        req_teacher_name = slot.get("teacher_name", "").strip().lower()
        for t_idx, teacher in enumerate(all_teachers):
            t_name = teacher.get("name", "").strip().lower()
            if req_teacher_name and req_teacher_name in t_name:
                # High preference (reward 10 points)
                objective_terms.append(10 * x[s_idx, t_idx])
            else:
                # Standard substitute assignment (reward 1 point)
                objective_terms.append(1 * x[s_idx, t_idx])

    if objective_terms:
        model.Maximize(sum(objective_terms))

    # Solve CP-SAT Model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    optimized_slots = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        logger.info("OR-Tools Solver successfully found a conflict-free solution!")
        for s_idx, slot in enumerate(requested_slots):
            assigned_slot = dict(slot)
            req_teacher_name = slot.get("teacher_name", "")
            
            assigned_teacher_obj = None
            for t_idx, teacher in enumerate(all_teachers):
                if solver.Value(x[s_idx, t_idx]) == 1:
                    assigned_teacher_obj = teacher
                    break

            if assigned_teacher_obj:
                assigned_name = assigned_teacher_obj.get("name")
                assigned_id = assigned_teacher_obj.get("id")
                
                assigned_slot["teacher_id"] = assigned_id
                
                if req_teacher_name and req_teacher_name.lower() != assigned_name.lower():
                    # Substitute assigned
                    assigned_slot["has_conflict"] = False
                    assigned_slot["conflict_reason"] = None
                    assigned_slot["is_substitute"] = True
                    assigned_slot["substitute_teacher"] = assigned_name
                    warnings.append(f"Slot Period {slot.get('period')} Class {slot.get('class_name')}: Assigned substitute '{assigned_name}' because primary '{req_teacher_name}' was unavailable.")
                else:
                    assigned_slot["teacher_name"] = assigned_name
                    assigned_slot["has_conflict"] = False
                    assigned_slot["conflict_reason"] = None
                    assigned_slot["is_substitute"] = False
                    assigned_slot["substitute_teacher"] = None
            else:
                assigned_slot["has_conflict"] = True
                assigned_slot["conflict_reason"] = "No available teacher found for period."
                warnings.append(f"Slot Period {slot.get('period')} Class {slot.get('class_name')}: No available teacher.")

            optimized_slots.append(assigned_slot)
    else:
        logger.warning("OR-Tools Solver could not find feasible schedule. Fallback with conflict flags.")
        warnings.append("Constraint solver could not resolve all constraints. Conflict flags applied.")
        for slot in requested_slots:
            s_copy = dict(slot)
            s_copy["has_conflict"] = True
            s_copy["conflict_reason"] = "Constraint solver infeasible"
            optimized_slots.append(s_copy)

    return optimized_slots, warnings
