from flask import Flask, render_template, request, jsonify, flash
from owlready2 import *
import json
import os

app = Flask(__name__)
app.secret_key = 'rehab_secret_key_2024'

def load_ontology():
    try:
        onto = get_ontology("ontology/rehabilitation.owx").load()
        print("✅ Онтология загружена успешно!")
        
        print(f"Классы: {list(onto.classes())}")
        print(f"Пациенты: {list(onto.Patient.instances())}")
        
        return onto
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None

onto = load_ontology()

class RehabilitationSystem:
    def __init__(self, ontology):
        self.onto = ontology
        self.condition_mapping = {
            'инсульт': ['patient_stroke_mild', 'patient_stroke_severe'],
            'травма позвоночника': ['patient_spinal_injury'],
            'артрит': ['patient_arthritis'],
            'дцп': ['patient_cerebral_palsy'],
            'после операции': ['patient_post_surgery'],
            'спортивная травма': ['patient_sports_injury'],
            'возрастные изменения': ['patient_age_related']
        }
        
        self.severity_mapping = {
            'легкая': 'Легкая',
            'средняя': 'Средняя', 
            'тяжелая': 'Тяжелая'
        }
        
        self.age_mapping = {
            'детский': 'Детский',
            'взрослый': 'Взрослый',
            'пожилой': 'Пожилой'
        }

    def get_all_programs(self):
        """Получить все программы реабилитации"""
        programs = []
        for program in self.onto.RehabilitationProgram.instances():
            program_info = {
                'name': program.name,
                'display_name': self._format_name(program.name),
                'duration': program.hasDuration[0] if program.hasDuration else 0,
                'session_count': program.hasSessionCount[0] if program.hasSessionCount else 0,
                'methods': [self._format_name(method.name) for method in program.includesMethod],
                'specialists': [self._format_name(spec.name) for spec in program.supervisedBy],
                'suitable_patients': [self._format_name(patient.name) for patient in program.suitableFor]
            }
            programs.append(program_info)
        return programs

    def find_optimal_programs(self, patient_data):
        """Подбор оптимальных программ реабилитации"""
        try:
            suitable_patient_types = self._find_suitable_patient_types(patient_data)
            
            if not suitable_patient_types:
                return []

            suitable_programs = []
            
            for program in self.onto.RehabilitationProgram.instances():
                program_patients = [patient.name for patient in program.suitableFor]
                
                matching_patients = set(program_patients) & set(suitable_patient_types)
                
                if matching_patients:
                    suitability_score = self._calculate_suitability_score(
                        program, patient_data, len(matching_patients)
                    )
                    
                    program_info = {
                        'program': program,
                        'score': suitability_score,
                        'matching_patients': [self._format_name(p) for p in matching_patients],
                        'methods': [self._format_name(method.name) for method in program.includesMethod],
                        'specialists': [self._format_name(spec.name) for spec in program.supervisedBy],
                        'duration': program.hasDuration[0] if program.hasDuration else 'Не указано',
                        'session_count': program.hasSessionCount[0] if program.hasSessionCount else 'Не указано'
                    }
                    suitable_programs.append(program_info)

            suitable_programs.sort(key=lambda x: x['score'], reverse=True)
            return suitable_programs[:5]
            
        except Exception as e:
            print(f"Ошибка при подборе программ: {e}")
            return []

    def _find_suitable_patient_types(self, patient_data):
        """Находим подходящие типы пациентов из онтологии"""
        diagnosis = patient_data['diagnosis'].lower()
        severity = self.severity_mapping.get(patient_data['severity'], '')
        age_group = self.age_mapping.get(patient_data['age_group'], '')
        
        suitable_types = []
        
        base_types = self.condition_mapping.get(diagnosis, [])
        
        for patient_type in base_types:
            patient_instance = self.onto.search_one(iri=f"*#{patient_type}")
            if patient_instance:
                patient_severity = patient_instance.hasSeverity[0] if patient_instance.hasSeverity else ''
                patient_age = patient_instance.hasAgeGroup[0] if patient_instance.hasAgeGroup else ''
                
                if (not severity or patient_severity == severity) and \
                   (not age_group or patient_age == age_group):
                    suitable_types.append(patient_type)
        
        return suitable_types if suitable_types else base_types

    def _calculate_suitability_score(self, program, patient_data, matching_count):
        """Расчет балла соответствия программы"""
        score = matching_count * 25
        
        goals = patient_data.get('goals', [])
        program_methods = [method.name for method in program.includesMethod]
        
        goal_bonus = 0
        for goal in goals:
            if self._goal_matches_methods(goal, program_methods):
                goal_bonus += 10
                
        score += goal_bonus
        
        mobility = patient_data.get('mobility_restrictions', '')
        if mobility == 'тяжелая' and 'method_mechanotherapy_robot' in program_methods:
            score += 15
        elif mobility == 'легкая' and 'method_exercise_therapy' in program_methods:
            score += 10
            
        return min(score, 100)

    def _goal_matches_methods(self, goal, methods):
        """Проверка соответствия целей методам"""
        goal_method_map = {
            'walking': ['method_exercise_therapy', 'method_mechanotherapy_robot'],
            'mobility': ['method_physiotherapy_electro', 'method_physiotherapy_magnet'],
            'pain_relief': ['method_physiotherapy_electro', 'method_massage'],
            'coordination': ['method_exercise_therapy', 'method_occupational_therapy'],
            'psychological': ['method_psychological_cbt'],
            'daily_activities': ['method_occupational_therapy']
        }
        
        required_methods = goal_method_map.get(goal, [])
        return any(method in methods for method in required_methods)

    def _format_name(self, name):
        """Форматирование имени для отображения"""
        return name.replace('_', ' ').title()

    def get_program_details(self, program_name):
        """Получить детальную информацию о программе"""
        program = self.onto.search_one(iri=f"*#{program_name}")
        if not program:
            return None
            
        return {
            'name': program.name,
            'display_name': self._format_name(program.name),
            'duration': program.hasDuration[0] if program.hasDuration else 'Не указано',
            'session_count': program.hasSessionCount[0] if program.hasSessionCount else 'Не указано',
            'methods': [{
                'name': self._format_name(method.name),
                'effectiveness': method.hasEffectivenessScore[0] if method.hasEffectivenessScore else 'Не указано'
            } for method in program.includesMethod],
            'specialists': [self._format_name(spec.name) for spec in program.supervisedBy],
            'suitable_patients': [self._format_name(patient.name) for patient in program.suitableFor]
        }

if onto:
    rehab_system = RehabilitationSystem(onto)
else:
    rehab_system = None
    print("ВНИМАНИЕ: Онтология не загружена!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patient-form')
def patient_form():
    return render_template('patient_form.html')

@app.route('/find-program', methods=['POST'])
def find_program():
    if not rehab_system:
        flash('Ошибка: система не загружена', 'error')
        return render_template('patient_form.html')
    
    try:
        patient_data = {
            'diagnosis': request.form['diagnosis'],
            'severity': request.form['severity'],
            'age_group': request.form['age_group'],
            'goals': request.form.getlist('goals'),
            'mobility_restrictions': request.form.get('mobility_restrictions', ''),
            'pain_level': request.form.get('pain_level', '')
        }
        
        optimal_programs = rehab_system.find_optimal_programs(patient_data)
        
        formatted_programs = []
        for program in optimal_programs:
            formatted_programs.append({
                'name': program['program'].name,
                'display_name': rehab_system._format_name(program['program'].name),
                'score': program['score'],
                'methods': program['methods'],
                'specialists': program['specialists'],
                'duration': program['duration'],
                'session_count': program['session_count'],
                'matching_patients': program['matching_patients']
            })
        
        return render_template('results.html', 
                             programs=formatted_programs,
                             patient_data=patient_data)
    
    except Exception as e:
        flash(f'Ошибка при обработке запроса: {str(e)}', 'error')
        return render_template('patient_form.html')

@app.route('/all-programs')
def all_programs():
    if not rehab_system:
        flash('Ошибка: система не загружена', 'error')
        return render_template('index.html')
    
    programs = rehab_system.get_all_programs()
    return render_template('all_programs.html', programs=programs)

@app.route('/program/<program_name>')
def program_detail(program_name):
    if not rehab_system:
        flash('Ошибка: система не загружена', 'error')
        return render_template('index.html')
    
    program = rehab_system.get_program_details(program_name)
    if not program:
        flash('Программа не найдена', 'error')
        return render_template('all_programs.html')
    
    return render_template('program_detail.html', program=program)

@app.route('/api/programs')
def api_programs():
    if not rehab_system:
        return jsonify({'error': 'System not loaded'}), 500
    
    programs = rehab_system.get_all_programs()
    return jsonify(programs)

@app.route('/api/find-program', methods=['POST'])
def api_find_program():
    if not rehab_system:
        return jsonify({'error': 'System not loaded'}), 500
    
    try:
        patient_data = request.get_json()
        programs = rehab_system.find_optimal_programs(patient_data)
        
        simplified_programs = []
        for program in programs:
            simplified_programs.append({
                'name': program['program'].name,
                'display_name': rehab_system._format_name(program['program'].name),
                'score': program['score'],
                'methods': program['methods'],
                'specialists': program['specialists'],
                'duration': program['duration']
            })
        
        return jsonify({'programs': simplified_programs})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)