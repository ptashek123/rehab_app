from flask import Flask, render_template, request, jsonify, flash
from owlready2 import *
import os

app = Flask(__name__)
app.secret_key = 'rehab_secret_key_2024'

def load_ontology():
    try:
        onto_path.append("ontology")
        onto = get_ontology("rehabilitation.owx").load()
        print("✅ Онтология загружена успешно!")
        return onto
    except Exception as e:
        print(f"❌ Ошибка загрузки онтологии: {e}")
        return None

onto = load_ontology()

class RehabilitationSystem:
    def __init__(self, ontology):
        self.onto = ontology
        if ontology:
            print("Система реабилитации инициализирована")
        else:
            print("ВНИМАНИЕ: Онтология не загружена!")
        
        self.condition_mapping = {
            'инсульт': ['Пациент_Инсульт_Легкий', 'Пациент_Инсульт_Тяжелый'],
            'травма позвоночника': ['Пациент_Травма_Позвоночника'],
            'артрит': ['Пациент_Артрит'],
            'дцп': ['Пациент_ДЦП'],
            'после операции': ['Пациент_После_Операции'],
            'спортивная травма': ['Пациент_Спортивная_Травма'],
            'возрастные изменения': ['Пациент_Возрастные_Изменения']
        }

    def get_russian_label(self, entity):
        try:
            if hasattr(entity, 'comment') and entity.comment:
                comments = entity.comment if isinstance(entity.comment, list) else [entity.comment]
                for comment in comments:
                    if isinstance(comment, str) and comment.strip():
                        return comment
            return entity.name.replace('_', ' ').title()
        except:
            return entity.name if hasattr(entity, 'name') else str(entity)

    def get_all_programs(self):
        """Получить все программы реабилитации"""
        if not self.onto:
            return []
            
        programs = []
        for program in self.onto.search(type=self.onto.ПрограммаРеабилитации):
            program_info = {
                'name': program.name,
                'display_name': self.get_russian_label(program),
                'duration': program.имеетДлительность[0] if hasattr(program, 'имеетДлительность') and program.имеетДлительность else 0,
                'session_count': program.имеетКоличествоСеансов[0] if hasattr(program, 'имеетКоличествоСеансов') and program.имеетКоличествоСеансов else 0,
                'methods': [self.get_russian_label(method) for method in program.включаетМетод] if hasattr(program, 'включаетМетод') else [],
                'specialists': [self.get_russian_label(spec) for spec in program.курируется] if hasattr(program, 'курируется') else [],
                'suitable_patients': [self.get_russian_label(patient) for patient in program.подходитДля] if hasattr(program, 'подходитДля') else []
            }
            programs.append(program_info)
        return programs

    def find_optimal_programs(self, patient_data):
        """Подбор оптимальных программ реабилитации"""
        if not self.onto:
            return []
            
        try:
            diagnosis = patient_data['diagnosis'].lower()
            suitable_patient_names = self.condition_mapping.get(diagnosis, [])
            
            if not suitable_patient_names:
                return []

            suitable_programs = []
            
            for program in self.onto.search(type=self.onto.ПрограммаРеабилитации):
                program_patients = program.подходитДля if hasattr(program, 'подходитДля') else []
                program_patient_names = [p.name for p in program_patients]
                
                matching_patients = set(program_patient_names) & set(suitable_patient_names)
                
                if matching_patients:
                    suitability_score = len(matching_patients) * 25
                    
                    goals = patient_data.get('goals', [])
                    program_methods = [m.name for m in program.включаетМетод] if hasattr(program, 'включаетМетод') else []
                    
                    for goal in goals:
                        if self._goal_matches_methods(goal, program_methods):
                            suitability_score += 10
                    
                    suitability_score = min(suitability_score, 100)
                    
                    program_info = {
                        'program': program,
                        'score': suitability_score,
                        'matching_patients': [self.get_russian_label(self.onto.search_one(iri=f"*#{p}")) for p in matching_patients],
                        'methods': [self.get_russian_label(method) for method in program.включаетМетод] if hasattr(program, 'включаетМетод') else [],
                        'specialists': [self.get_russian_label(spec) for spec in program.курируется] if hasattr(program, 'курируется') else [],
                        'duration': program.имеетДлительность[0] if hasattr(program, 'имеетДлительность') and program.имеетДлительность else 'Не указано',
                        'session_count': program.имеетКоличествоСеансов[0] if hasattr(program, 'имеетКоличествоСеансов') and program.имеетКоличествоСеансов else 'Не указано'
                    }
                    suitable_programs.append(program_info)

            suitable_programs.sort(key=lambda x: x['score'], reverse=True)
            return suitable_programs[:5]
            
        except Exception as e:
            print(f"Ошибка при подборе программ: {e}")
            return []

    def _goal_matches_methods(self, goal, methods):
        """Проверка соответствия целей методам"""
        goal_method_map = {
            'walking': ['Метод_ЛФК', 'Метод_Механотерапия_Робот'],
            'mobility': ['Метод_Физиотерапия_Электро', 'Метод_Физиотерапия_Магнит'],
            'pain_relief': ['Метод_Физиотерапия_Электро', 'Метод_Массаж'],
            'coordination': ['Метод_ЛФК', 'Метод_Эрготерапия'],
            'psychological': ['Метод_Психологическая_Терапия'],
            'daily_activities': ['Метод_Эрготерапия']
        }
        
        required_methods = goal_method_map.get(goal, [])
        return any(method in methods for method in required_methods)

    def get_program_details(self, program_name):
        """Получить детальную информацию о программе"""
        if not self.onto:
            return None
            
        program = self.onto.search_one(iri=f"*#{program_name}")
        if not program:
            return None
            
        return {
            'name': program.name,
            'display_name': self.get_russian_label(program),
            'duration': program.имеетДлительность[0] if hasattr(program, 'имеетДлительность') and program.имеетДлительность else 'Не указано',
            'session_count': program.имеетКоличествоСеансов[0] if hasattr(program, 'имеетКоличествоСеансов') and program.имеетКоличествоСеансов else 'Не указано',
            'methods': [{
                'name': self.get_russian_label(method),
                'effectiveness': method.имеетЭффективность[0] if hasattr(method, 'имеетЭффективность') and method.имеетЭффективность else 'Не указано'
            } for method in program.включаетМетод] if hasattr(program, 'включаетМетод') else [],
            'specialists': [self.get_russian_label(spec) for spec in program.курируется] if hasattr(program, 'курируется') else [],
            'suitable_patients': [self.get_russian_label(patient) for patient in program.подходитДля] if hasattr(program, 'подходитДля') else []
        }

rehab_system = RehabilitationSystem(onto)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patient-form')
def patient_form():
    return render_template('patient_form.html')

@app.route('/find-program', methods=['POST'])
def find_program():
    if not rehab_system.onto:
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
                'display_name': program['display_name'] if 'display_name' in program else rehab_system.get_russian_label(program['program']),
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
    programs = rehab_system.get_all_programs()
    return render_template('all_programs.html', programs=programs)

@app.route('/program/<program_name>')
def program_detail(program_name):
    program = rehab_system.get_program_details(program_name)
    if not program:
        flash('Программа не найдена', 'error')
        return render_template('all_programs.html')
    
    return render_template('program_detail.html', program=program)

if __name__ == '__main__':
    port = 5001
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)