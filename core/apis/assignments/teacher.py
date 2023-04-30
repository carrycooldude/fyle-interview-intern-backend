from core import db
from flask import Blueprint, jsonify, request
from core.models.assignments import Assignment
from core.models.assignments import AssignmentStateEnum
from core.apis.decorators import auth_principal , Principal
from core.libs import assertions

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/assignments', methods=['GET'])
@auth_principal
def get_assignments(principal : Principal):
    if not principal.teacher_id:
        return jsonify({'error': 'User is not a teacher'}), 400

    assignments = Assignment.filter(Assignment.teacher_id == principal.teacher_id).all()
    response_data = [{'id': assignment.id,
                      'content': assignment.content,
                      'created_at': assignment.created_at.isoformat(),
                      'updated_at': assignment.updated_at.isoformat(),
                      'state': assignment.state.value,
                      'grade': assignment.grade,
                      'student_id': assignment.student_id,
                      'teacher_id': assignment.teacher_id} for assignment in assignments]

    return jsonify({'data': response_data}), 200


@teacher_bp.route('/assignments/grade', methods=['POST'])
@auth_principal
def grade_assignment(principal : Principal):
    if not principal.teacher_id:
        return jsonify({'error': 'User is not a teacher'}), 400

    data = request.get_json()
    assignment_id = data.get('id')
    grade = data.get('grade')

    assertions.assert_valid(assignment_id is not None, 'assignment id is required')
    assertions.assert_valid(grade in [grade.value for grade in AssignmentStateEnum.__members__.values()], 'invalid grade')

    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({'error': 'No assignment with this id was found'}), 404

    assertions.assert_valid(assignment.teacher_id == principal.teacher_id, 'This assignment does not belong to this teacher')
    assertions.assert_valid(assignment.state == AssignmentStateEnum.SUBMITTED, 'This assignment cannot be graded')

    assignment.grade = grade
    assignment.state = AssignmentStateEnum.GRADED
    db.session.commit()

    response_data = {'id': assignment.id,
                     'content': assignment.content,
                     'created_at': assignment.created_at.isoformat(),
                     'updated_at': assignment.updated_at.isoformat(),
                     'state': assignment.state.value,
                     'grade': assignment.grade,
                     'student_id': assignment.student_id,
                     'teacher_id': assignment.teacher_id}

    return jsonify({'data': response_data}), 200
