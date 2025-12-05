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
        print("Система реабилитации инициализирована")
        
        self.condition_mapping = {
            'инсульт': ['patient_stroke_mild', 'patient_stroke_severe', 'Пациент_Инсульт_Легкий', 'Пациент_Инсульт_Тяжелый'],
            'травма позвоночника': ['patient_spinal_injury', 'Пациент_Травма_Позвоночника'],
            'артрит': ['patient_arthritis', 'Пациент_Артрит'],
            'дцп': ['patient_cerebral_palsy', 'Пациент_ДЦП'],
            'после операции': ['patient_post_surgery', 'Пациент_После_Операции'],
            'спортивная травма': ['patient_sports_injury', 'Пациент_Спортивная_Травма'],
            'возрастные изменения': ['patient_age_related', 'Пациент_Возрастные_Изменения']
        }
        
        self.movement_impairment_mapping = {
            'none': 'Нет ограничений',
            'mild': 'Легкая',
            'medium': 'Средняя', 
            'severe': 'Тяжелая',
        }
        
        self.target_translation = {
            'walking': 'Ходьба',
            'balance': 'Баланс',
            'strength': 'Сила',
            'flexibility': 'Гибкость',
            'endurance': 'Выносливость',
            'coordination': 'Координация',
            'pain_reduction': 'Снижение боли',
            'independence': 'Самостоятельность'
        }
        
        self.goal_translation = {
            'walking': 'Ходьба',
            'mobility': 'Подвижность', 
            'pain_relief': 'Снятие боли',
            'coordination': 'Координация',
            'psychological': 'Психологическая поддержка',
            'daily_activities': 'Бытовые навыки'
        }
        
        self.method_translation = {
            'method_physiotherapy_electro': 'Электрофорез',
            'method_physiotherapy_magnet': 'Магнитотерапия',
            'method_exercise_therapy': 'Лечебная физкультура',
            'method_mechanotherapy_robot': 'Роботизированная терапия',
            'method_hydrotherapy': 'Гидротерапия',
            'method_occupational_therapy': 'Эрготерапия',
            'method_psychological_cbt': 'Когнитивно-поведенческая терапия',
            'method_massage': 'Массаж'
        }

    def get_all_programs(self):
        """Получить все программы реабилитации"""
        if not self.onto:
            return []
            
        programs = []
        try:
            program_class = None
            for cls in self.onto.classes():
                if 'Программа' in str(cls) or 'Program' in str(cls):
                    program_class = cls
                    break
            
            if program_class:
                all_instances = list(program_class.instances())
            else:
                all_instances = []
                for cls in self.onto.classes():
                    for inst in cls.instances():
                        if 'program' in str(inst).lower() or 'программа' in str(inst).lower():
                            all_instances.append(inst)
            
            print(f"Найдено {len(all_instances)} программ")
            
            for program in all_instances:
                try:
                    program_info = {
                        'name': program.name,
                        'display_name': self._get_display_name(program),
                        'duration': self._get_property(program, 'hasDuration', 'имеетДлительность'),
                        'session_count': self._get_property(program, 'hasSessionCount', 'имеетКоличествоСеансов'),
                        'methods': self._get_related(program, 'includesMethod', 'включаетМетод'),
                        'specialists': self._get_related(program, 'supervisedBy', 'курируется'),
                        'suitable_patients': self._get_related(program, 'suitableFor', 'подходитДля'),
                        'target': self._get_related(program, 'hasTarget', 'имеетЦелевуюГруппу'),
                        'movement_impairemet': self._get_property(program, 'suitableMovementImpairment', 'подходитДляУровняДвижения')
                    }
                    programs.append(program_info)
                except Exception as e:
                    print(f"Ошибка при обработке программы {program}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Ошибка в get_all_programs: {e}")
            import traceback
            traceback.print_exc()
            
        return programs

    def _get_display_name(self, entity):
        """Получить отображаемое имя"""
        try:
            if hasattr(entity, 'comment') and entity.comment:
                comment = entity.comment[0] if isinstance(entity.comment, list) else entity.comment
                if comment and str(comment).strip():
                    return str(comment)
            
            if hasattr(entity, 'label') and entity.label:
                label = entity.label[0] if isinstance(entity.label, list) else entity.label
                if label and str(label).strip():
                    return str(label)
            
            name = entity.name
            name = name.replace('_', ' ')
            name = name.replace('program', '')
            name = name.replace('Program', '')
            name = name.replace('программа', '')
            name = name.replace('Программа', '')
            return name.strip().title()
            
        except:
            return entity.name if hasattr(entity, 'name') else str(entity)

    def _get_property(self, entity, *property_names):
        """Получить значение свойства"""
        for prop_name in property_names:
            if hasattr(entity, prop_name):
                value = getattr(entity, prop_name)
                if value:
                    if isinstance(value, list):
                        return value[0] if value else 'Не указано'
                    return value
        return 'Не указано'

    def _get_related(self, entity, *property_names):
        """Получить связанные сущности"""
        result = []
        for prop_name in property_names:
            if hasattr(entity, prop_name):
                related = getattr(entity, prop_name)
                if related:
                    if isinstance(related, list):
                        for item in related:
                            if item:
                                display_name = self._get_display_name(item)
                                result.append(display_name)
                    else:
                        if related:
                            display_name = self._get_display_name(related)
                            result.append(display_name)
        return result

    def find_optimal_programs(self, patient_data):
        """Подбор оптимальных программ реабилитации с учетом новых свойств"""
        if not self.onto:
            print("Онтология не загружена")
            return []
            
        try:
            diagnosis = patient_data['diagnosis'].lower()
            movement_impairment = patient_data.get('movement_impairment', '').lower()
            target = patient_data.get('target', '')
            
            print(f"Данные пациента: диагноз={diagnosis}, нарушение движения={movement_impairment}, цель={target}")
            
            possible_patient_names = self.condition_mapping.get(diagnosis, [])
            print(f"Возможные имена пациентов: {possible_patient_names}")
            
            all_programs = self.get_all_programs()
            print(f"Всего программ в системе: {len(all_programs)}")
            
            suitable_programs = []
            
            for program_info in all_programs:
                program_name = program_info['name']
                print(f"\nАнализируем программу: {program_name}")
                
                program = self.onto.search_one(iri=f"*#{program_name}")
                if not program:
                    print(f"  Программа {program_name} не найдена в онтологии")
                    continue
                
                program_patients = self._get_related(program, 'suitableFor', 'подходитДля')
                print(f"  Пациенты программы: {program_patients}")
                
                matches_diagnosis = False
                for patient_display_name in program_patients:
                    for patient in self.onto.individuals():
                        if hasattr(patient, 'name'):
                            patient_display = self._get_display_name(patient)
                            if patient_display == patient_display_name:
                                for possible_name in possible_patient_names:
                                    if possible_name in patient.name or possible_name in patient_display:
                                        matches_diagnosis = True
                                        print(f"  ✓ Совпадение по диагнозу: {patient.name}")
                                        break
                
                if not matches_diagnosis:
                    print(f"  ✗ Не подходит по диагнозу")
                    continue
                
                base_score = 50
                
                goals = patient_data.get('goals', [])
                program_methods = program_info['methods']
                
                for goal in goals:
                    if self._goal_matches_methods(goal, program_methods):
                        base_score += 10
                        print(f"  +10 баллов: цель '{goal}' совпадает с методами программы")
                
                severity = patient_data.get('severity', '')
                if severity == 'тяжелая' and any('робот' in method.lower() for method in program_methods):
                    base_score += 15
                    print(f"  +15 баллов: тяжелое состояние + роботизированная терапия")
                elif severity == 'легкая' and any('лфк' in method.lower() for method in program_methods):
                    base_score += 10
                    print(f"  +10 баллов: легкое состояние + ЛФК")
                
                if movement_impairment:
                    movement_match_score = self._check_movement_impairment_match(
                        movement_impairment, 
                        program_info.get('movement_impairment', ''),
                        program_methods
                    )
                    base_score += movement_match_score
                    if movement_match_score > 0:
                        print(f"  +{movement_match_score} баллов: совпадение по уровню движения")
                
                if target:
                    target_match_score = self._check_target_match(
                        target,
                        program_info.get('target', []),
                        program_methods
                    )
                    base_score += target_match_score
                    if target_match_score > 0:
                        print(f"  +{target_match_score} баллов: совпадение по цели реабилитации")
                
                patient_specific_score = self._check_patient_specific_match(
                    diagnosis, movement_impairment, target, program
                )
                base_score += patient_specific_score
                if patient_specific_score > 0:
                    print(f"  +{patient_specific_score} баллов: специфическое соответствие пациенту")
                
                score = min(base_score, 100)
                
                program_info['score'] = score
                program_info['matching_patients'] = program_patients
                program_info['movement_match'] = movement_impairment if movement_impairment else 'Не указано'
                program_info['target_match'] = self.target_translation.get(target, target) if target else 'Не указано'
                
                suitable_programs.append(program_info)
                print(f"  Итоговый балл: {score}")
            
            suitable_programs.sort(key=lambda x: x.get('score', 0), reverse=True)
            print(f"\nВсего найдено подходящих программ: {len(suitable_programs)}")
            
            return suitable_programs[:5]
            
        except Exception as e:
            print(f"Ошибка в find_optimal_programs: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _check_movement_impairment_match(self, patient_impairment, program_movement_impairment, program_methods):
        """Проверка соответствия уровня нарушения движения"""
        score = 0
        
        impairment_method_map = {
            'severe': ['роботизированная терапия', 'гидротерапия', 'массаж'],
            'paralysis': ['роботизированная терапия', 'электрофорез', 'магнитотерапия'],
            'moderate': ['лфк', 'эрготерапия', 'массаж'],
            'mild': ['лфк', 'физиотерапия', 'упражнения'],
            'none': ['упражнения', 'профилактика']
        }
        
        if program_movement_impairment:
            program_level_lower = program_movement_impairment.lower()
            patient_level_lower = patient_impairment.lower()
            
            level_compatibility = {
                'severe': ['severe', 'paralysis', 'moderate'],
                'moderate': ['moderate', 'mild', 'severe'],
                'mild': ['mild', 'none', 'moderate'],
                'none': ['none', 'mild']
            }
            
            if patient_level_lower in level_compatibility.get(program_level_lower, []):
                score += 10
        
        suitable_methods = impairment_method_map.get(patient_impairment, [])
        program_methods_lower = [m.lower() for m in program_methods]
        
        for method in suitable_methods:
            if any(method in pm for pm in program_methods_lower):
                score += 5
                break
        
        return score

    def _check_target_match(self, patient_target, program_target, program_methods):
        """Проверка соответствия цели реабилитации"""
        score = 0
        
        # Маппинг целей к методам
        target_method_map = {
            'walking': ['роботизированная терапия', 'лфк', 'ходьба'],
            'balance': ['упражнения на баланс', 'лфк', 'физиотерапия'],
            'strength': ['силовые упражнения', 'лфк', 'тренажеры'],
            'flexibility': ['растяжка', 'йога', 'пилатес'],
            'coordination': ['эрготерапия', 'упражнения на координацию', 'лфк'],
            'pain_reduction': ['массаж', 'физиотерапия', 'гидротерапия']
        }
        
        if program_target:
            program_targets_lower = [t.lower() for t in program_target]
            patient_target_lower = patient_target.lower()
            patient_target_translated = self.target_translation.get(patient_target, patient_target).lower()
            
            for program_target in program_targets_lower:
                if (patient_target_lower in program_target or 
                    patient_target_translated in program_target or
                    any(word in program_target for word in patient_target_lower.split('_'))):
                    score += 10
                    break
        
        suitable_methods = target_method_map.get(patient_target, [])
        program_methods_lower = [m.lower() for m in program_methods]
        
        for method in suitable_methods:
            if any(method in pm for pm in program_methods_lower):
                score += 5
                break
        
        return score

    def _check_patient_specific_match(self, diagnosis, movement_impairment, target, program):
        """Проверка специфического соответствия конкретному пациенту в онтологии"""
        score = 0
        
        try:
            all_patients = []
            for cls in self.onto.classes():
                if 'Пациент' in str(cls) or 'Patient' in str(cls):
                    all_patients.extend(cls.instances())
            
            for patient in all_patients:
                patient_diagnosis_matches = False
                for possible_name in self.condition_mapping.get(diagnosis, []):
                    if possible_name in patient.name:
                        patient_diagnosis_matches = True
                        break
                
                if not patient_diagnosis_matches:
                    continue
                
                patient_movement = ''
                if hasattr(patient, 'hasMovementImpairment'):
                    movement_value = getattr(patient, 'hasMovementImpairment')
                    if movement_value:
                        if isinstance(movement_value, list):
                            patient_movement = str(movement_value[0]).lower()
                        else:
                            patient_movement = str(movement_value).lower()
                
                patient_target = ''
                if hasattr(patient, 'hasTarget'):
                    target_value = getattr(patient, 'hasTarget')
                    if target_value:
                        if isinstance(target_value, list):
                            patient_target = str(target_value[0]).lower()
                        else:
                            patient_target = str(target_value).lower()
                
                if hasattr(program, 'suitableFor') or hasattr(program, 'подходитДля'):
                    suitable_for = getattr(program, 'suitableFor', []) or getattr(program, 'подходитДля', [])
                    if not isinstance(suitable_for, list):
                        suitable_for = [suitable_for]
                    
                    for suitable_patient in suitable_for:
                        if patient.name == suitable_patient.name:
                            score += 5
                            
                            if movement_impairment and patient_movement and movement_impairment in patient_movement:
                                score += 5
                            
                            if target and patient_target and target in patient_target:
                                score += 5
                            
                            return score
        
        except Exception as e:
            print(f"Ошибка в проверке специфического соответствия: {e}")
        
        return score

    def _goal_matches_methods(self, goal, methods):
        """Проверка соответствия целей методам"""
        method_strings = [str(m).lower() for m in methods]
        
        goal_method_map = {
            'walking': ['лфк', 'exercise', 'механотерапия', 'робот', 'ходьба'],
            'mobility': ['физиотерапия', 'physiotherapy', 'электро', 'магнит', 'подвижность'],
            'pain_relief': ['физиотерапия', 'массаж', 'massage', 'обезболивание'],
            'coordination': ['лфк', 'эрготерапия', 'occupational', 'координация'],
            'psychological': ['психологическая', 'психология', 'psychological', 'кпт', 'психотерапия'],
            'daily_activities': ['эрготерапия', 'occupational', 'бытовые', 'повседневные']
        }
        
        required_methods = goal_method_map.get(goal, [])
        for required in required_methods:
            for method in method_strings:
                if required in method:
                    return True
        return False

    def translate_goals(self, goals):
        """Перевод целей на русский"""
        return [self.goal_translation.get(goal, goal) for goal in goals]

    def get_program_details(self, program_name):
        """Получить детальную информацию о программе"""
        if not self.onto:
            return None
            
        try:
            program = self.onto.search_one(iri=f"*#{program_name}")
            if not program:
                return None
            
            methods_with_effectiveness = []
            if hasattr(program, 'includesMethod') or hasattr(program, 'включаетМетод'):
                methods = getattr(program, 'includesMethod', []) or getattr(program, 'включаетМетод', [])
                if not isinstance(methods, list):
                    methods = [methods]
                    
                for method in methods:
                    if method:
                        effectiveness = 'Не указано'
                        if hasattr(method, 'hasEffectivenessScore'):
                            eff_value = method.hasEffectivenessScore
                            if eff_value:
                                effectiveness = eff_value[0] if isinstance(eff_value, list) else eff_value
                        elif hasattr(method, 'имеетЭффективность'):
                            eff_value = method.имеетЭффективность
                            if eff_value:
                                effectiveness = eff_value[0] if isinstance(eff_value, list) else eff_value
                        
                        methods_with_effectiveness.append({
                            'name': self._get_display_name(method),
                            'effectiveness': effectiveness
                        })
            
            return {
                'name': program.name,
                'display_name': self._get_display_name(program),
                'duration': self._get_property(program, 'hasDuration', 'имеетДлительность'),
                'session_count': self._get_property(program, 'hasSessionCount', 'имеетКоличествоСеансов'),
                'methods': methods_with_effectiveness,
                'specialists': self._get_related(program, 'supervisedBy', 'курируется'),
                'suitable_patients': self._get_related(program, 'suitableFor', 'подходитДля'),
                'target': self._get_related(program, 'hasTargetGroup', 'имеетЦелевуюГруппу'),
                'movement_impairment': self._get_property(program, 'suitableMovementLevel', 'подходитДляУровняДвижения')
            }
            
        except Exception as e:
            print(f"Ошибка в get_program_details: {e}")
            return None

rehab_system = RehabilitationSystem(onto)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patient-form')
def patient_form():
    return render_template('patient_form.html')

@app.route('/find-program', methods=['POST'])
def find_program():
    try:
        patient_data = {
            'diagnosis': request.form['diagnosis'],
            'severity': request.form['severity'],
            'age_group': request.form['age_group'],
            'goals': request.form.getlist('goals'),
            'mobility_restrictions': request.form.get('mobility_restrictions', ''),
            'pain_level': request.form.get('pain_level', ''),
            'movement_impairment': request.form.get('movement_impairment', ''),
            'target': request.form.get('target', '')
        }
        
        print(f"Данные пациента: {patient_data}")
        
        optimal_programs = rehab_system.find_optimal_programs(patient_data)
        
        translated_goals = rehab_system.translate_goals(patient_data['goals'])
        
        return render_template('results.html', 
                             programs=optimal_programs,
                             patient_data=patient_data,
                             translated_goals=translated_goals)
    
    except Exception as e:
        flash(f'Ошибка при обработке запроса: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return render_template('patient_form.html')

@app.route('/all-programs')
def all_programs():
    programs = rehab_system.get_all_programs()
    print(f"Всего программ для отображения: {len(programs)}")
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