from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owx").load()

def get_russian_name(entity):
    """Получить русское название из rdfs:comment или использовать label"""
    if hasattr(entity, 'comment') and entity.comment:
        russian_name = entity.comment.first()
        if russian_name:
            return russian_name
    
    if hasattr(entity, 'label') and entity.label:
        english_name = entity.label.first()
        if english_name:
            return english_name
    
    return entity.name

def get_entity_by_label(label):
    """Найти сущность по метке (rdfs:label)"""
    return onto.search_one(label=label)

def get_all_entities_by_class_label(class_label):
    """Получить все сущности по метке класса с русскими названиями"""
    entities = []
    try:
        target_class = get_entity_by_label(class_label)
        if target_class:
            for individual in target_class.instances():
                russian_name = get_russian_name(individual)
                if russian_name:
                    entities.append(russian_name)
            
            for subclass in target_class.subclasses():
                russian_name = get_russian_name(subclass)
                if russian_name and russian_name not in entities:
                    entities.append(russian_name)
                    
    except Exception as e:
        print(f"Error getting entities for {class_label}: {e}")
    
    return list(set(entities))

def find_matching_entities(selected_names, target_class_label):
    """Найти сущности в онтологии, которые соответствуют выбранным названиям"""
    matches = []
    try:
        target_class = get_entity_by_label(target_class_label)
        if not target_class:
            return matches
            
        all_entities = list(target_class.instances()) + list(target_class.subclasses())
        
        for entity in all_entities:
            entity_russian = get_russian_name(entity)
            if entity_russian in selected_names:
                matches.append(entity)
                print(f"Found match: {entity_russian} -> {entity}")
                
    except Exception as e:
        print(f"Error in find_matching_entities: {e}")
    
    return matches

def recommend_programs(selected_symptoms, selected_conditions):
    """Подбор программ на основе симптомов и состояний"""
    recommended_programs = []

    try:
        symptom_entities = find_matching_entities(selected_symptoms, "Symptom")
        condition_entities = find_matching_entities(selected_conditions, "MedicalCondition")
        
        print(f"Matching symptoms: {[get_russian_name(e) for e in symptom_entities]}")
        print(f"Matching conditions: {[get_russian_name(e) for e in condition_entities]}")

        rehab_class = get_entity_by_label("RehabProgram")
        if not rehab_class:
            print("RehabProgram class not found")
            return []
        
        all_programs = list(rehab_class.instances())
        print(f"Found {len(all_programs)} programs")

        recommended_prop = get_entity_by_label("isRecommendedFor")
        includes_prop = get_entity_by_label("includesMethod")
        contraindication_prop = get_entity_by_label("hasContraindication")

        print(f"Properties found - Recommended: {recommended_prop}, Includes: {includes_prop}")

        for program in all_programs:
            if not program:
                continue
            
            program_name = get_russian_name(program)
            if not program_name:
                continue

            print(f"\n=== Checking program: {program_name} ===")

            program_info = {
                'name': program_name,
                'methods': [],
                'recommended_for': [],
                'matches': []
            }

            if includes_prop:
                try:
                    methods = getattr(program, includes_prop.name, [])
                    if not isinstance(methods, list):
                        methods = [methods]
                    for method in methods:
                        if method:
                            method_name = get_russian_name(method)
                            if method_name:
                                program_info['methods'].append(method_name)
                    print(f"Methods: {program_info['methods']}")
                except Exception as e:
                    print(f"Error getting methods: {e}")

            is_recommended = False
            if recommended_prop:
                try:
                    recommendations = getattr(program, recommended_prop.name, [])
                    if not isinstance(recommendations, list):
                        recommendations = [recommendations]
                    
                    print(f"Program recommendations: {[get_russian_name(r) for r in recommendations if r]}")
                    
                    for rec in recommendations:
                        if rec:
                            rec_name = get_russian_name(rec)
                            if rec_name:
                                program_info['recommended_for'].append(rec_name)
                                
                                if rec in symptom_entities or rec in condition_entities:
                                    is_recommended = True
                                    match_type = "symptom" if rec in symptom_entities else "condition"
                                    program_info['matches'].append(f"{rec_name} ({match_type})")
                                    print(f"✓ Match found: {rec_name}")
                    
                except Exception as e:
                    print(f"Error getting recommendations: {e}")

            has_contraindication = False
            if contraindication_prop:
                try:
                    contraindications = getattr(program, contraindication_prop.name, [])
                    if not isinstance(contraindications, list):
                        contraindications = [contraindications]
                    
                    for contra in contraindications:
                        if contra and (contra in symptom_entities or contra in condition_entities):
                            has_contraindication = True
                            print(f"✗ Contraindication: {get_russian_name(contra)}")
                            break
                except Exception as e:
                    print(f"Error getting contraindications: {e}")

            if is_recommended and not has_contraindication:
                program_info['match_count'] = len(program_info['matches'])
                recommended_programs.append(program_info)
                print(f"✅ ADDED TO RECOMMENDATIONS: {program_name}")

    except Exception as e:
        print(f"Error in recommend_programs: {e}")

    return recommended_programs

@app.route('/')
def index():
    """Главная страница с формой выбора"""
    try:
        symptoms = get_all_entities_by_class_label("Symptom")
        conditions = get_all_entities_by_class_label("MedicalCondition")
        
        print(f"Loaded {len(symptoms)} symptoms: {symptoms}")
        print(f"Loaded {len(conditions)} conditions: {conditions}")
        
        if not symptoms:
            symptoms = ["Боль", "Ограниченная подвижность", "Мышечная слабость", "Депрессия"]
        if not conditions:
            conditions = ["Инсульт", "Травма позвоночника", "Травма сустава", "Неврологическое расстройство"]
            
    except Exception as e:
        print(f"Error loading ontology: {e}")
        symptoms = ["Боль", "Ограниченная подвижность", "Мышечная слабость", "Депрессия"]
        conditions = ["Инсульт", "Травма позвоночника", "Травма сустава", "Неврологическое расстройство"]
    
    return render_template('index.html', symptoms=symptoms, conditions=conditions)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Обработка формы и вывод результатов"""
    selected_symptoms = request.form.getlist('symptoms')
    selected_conditions = request.form.getlist('conditions')
    
    print(f"\n" + "="*50)
    print(f"SELECTED BY USER:")
    print(f"Symptoms: {selected_symptoms}")
    print(f"Conditions: {selected_conditions}")
    print("="*50)

    programs = recommend_programs(selected_symptoms, selected_conditions)
    
    print(f"\nFINAL RESULT: Found {len(programs)} recommended programs")

    return render_template('results.html', 
                         programs=programs,
                         selected_symptoms=selected_symptoms,
                         selected_conditions=selected_conditions)

if __name__ == '__main__':
    app.run(debug=True)