from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owx").load()

def extract_readable_name(entity):
    """Извлечь читаемое имя из сущности"""
    if hasattr(entity, 'comment') and entity.comment:
        comment = entity.comment.first()
        if comment and comment.strip():
            return comment.strip()
    
    if hasattr(entity, 'label') and entity.label:
        label = entity.label.first()
        if label and label.strip():
            return label.strip()
    
    name = entity.name
    if ':' in name:
        name = name.split(':')[-1]
    return name

def get_all_entities_directly():
    """Получить все сущности напрямую, без поиска по классам"""
    all_data = {
        'symptoms': set(),
        'conditions': set(),
        'programs': []
    }
    
    try:
        properties = {}
        for prop in onto.object_properties():
            prop_name = extract_readable_name(prop)
            properties[prop.name] = {
                'readable_name': prop_name,
                'object': prop
            }
            print(f"Property: {prop.name} -> {prop_name}")
        
        for individual in onto.individuals():
            individual_name = extract_readable_name(individual)
            individual_types = [extract_readable_name(t) for t in individual.is_a if hasattr(t, 'iri')]
            
            print(f"Individual: {individual_name} (types: {individual_types})")
            
            is_symptom = any('symptom' in str(t).lower() or 'симптом' in str(extract_readable_name(t)).lower() for t in individual.is_a)
            is_condition = any('condition' in str(t).lower() or 'состояние' in str(extract_readable_name(t)).lower() or 'medical' in str(t).lower() for t in individual.is_a)
            is_program = any('program' in str(t).lower() or 'програм' in str(extract_readable_name(t)).lower() or 'rehab' in str(t).lower() for t in individual.is_a)
            
            if is_symptom:
                all_data['symptoms'].add(individual_name)
            elif is_condition:
                all_data['conditions'].add(individual_name)
            elif is_program:
                program_data = {
                    'name': individual_name,
                    'object': individual,
                    'methods': [],
                    'recommendations': [],
                    'contraindications': []
                }
                
                for prop_name, prop_info in properties.items():
                    try:
                        values = getattr(individual, prop_name, [])
                        if not isinstance(values, list):
                            values = [values]
                        
                        for value in values:
                            if value:
                                value_name = extract_readable_name(value)
                                if 'method' in prop_info['readable_name'].lower() or 'метод' in prop_info['readable_name'].lower():
                                    program_data['methods'].append(value_name)
                                elif 'recommend' in prop_info['readable_name'].lower() or 'рекоменд' in prop_info['readable_name'].lower():
                                    program_data['recommendations'].append(value_name)
                                elif 'contraindicat' in prop_info['readable_name'].lower() or 'противопок' in prop_info['readable_name'].lower():
                                    program_data['contraindications'].append(value_name)
                    except Exception as e:
                        print(f"Error processing property {prop_name} for {individual_name}: {e}")
                
                all_data['programs'].append(program_data)
        
        all_data['symptoms'] = list(all_data['symptoms'])
        all_data['conditions'] = list(all_data['conditions'])
        
    except Exception as e:
        print(f"Error in get_all_entities_directly: {e}")
    
    return all_data

def recommend_programs_smart(selected_symptoms, selected_conditions, all_data):
    """Умный подбор программ с поиском по ключевым словам"""
    recommended_programs = []
    
    print(f"Selected: symptoms={selected_symptoms}, conditions={selected_conditions}")
    print(f"Available programs: {len(all_data['programs'])}")
    
    for program in all_data['programs']:
        print(f"\nChecking program: {program['name']}")
        print(f"  Recommendations: {program['recommendations']}")
        print(f"  Contraindications: {program['contraindications']}")
        
        has_recommendation = False
        matches = []
        
        for recommendation in program['recommendations']:
            for symptom in selected_symptoms:
                if symptom.lower() in recommendation.lower() or recommendation.lower() in symptom.lower():
                    has_recommendation = True
                    matches.append(f"симптом '{symptom}'")
                    print(f"  ✓ Matches symptom: {symptom} -> {recommendation}")
            
            for condition in selected_conditions:
                if condition.lower() in recommendation.lower() or recommendation.lower() in condition.lower():
                    has_recommendation = True
                    matches.append(f"состояние '{condition}'")
                    print(f"  ✓ Matches condition: {condition} -> {recommendation}")
        
        has_contraindication = False
        for contraindication in program['contraindications']:
            for symptom in selected_symptoms:
                if symptom.lower() in contraindication.lower() or contraindication.lower() in symptom.lower():
                    has_contraindication = True
                    print(f"  ✗ Contraindicated for symptom: {symptom} -> {contraindication}")
                    break
            
            for condition in selected_conditions:
                if condition.lower() in contraindication.lower() or contraindication.lower() in condition.lower():
                    has_contraindication = True
                    print(f"  ✗ Contraindicated for condition: {condition} -> {contraindication}")
                    break
            
            if has_contraindication:
                break
        
        if has_recommendation and not has_contraindication:
            program_info = {
                'name': program['name'],
                'methods': program['methods'],
                'recommended_for': program['recommendations'],
                'matches': matches
            }
            recommended_programs.append(program_info)
            print(f"  ✅ ADDED TO RECOMMENDATIONS")
    
    return recommended_programs

ontology_data = None

@app.route('/')
def index():
    """Главная страница с формой выбора"""
    global ontology_data
    
    try:
        if ontology_data is None:
            ontology_data = get_all_entities_directly()
        
        symptoms = ontology_data['symptoms']
        conditions = ontology_data['conditions']
        
        print(f"Loaded {len(symptoms)} symptoms: {symptoms}")
        print(f"Loaded {len(conditions)} conditions: {conditions}")
        print(f"Loaded {len(ontology_data['programs'])} programs")
        
        if not symptoms:
            symptoms = ["Боль", "Депрессия", "Ограниченная подвижность"]
        if not conditions:
            conditions = ["Инсульт", "Травма позвоночника", "Неврологическое расстройство"]
            
    except Exception as e:
        print(f"Error loading ontology: {e}")
        symptoms = ["Боль", "Депрессия", "Ограниченная подвижность"]
        conditions = ["Инсульт", "Травма позвоночника", "Неврологическое расстройство"]
        ontology_data = None
    
    return render_template('index.html', symptoms=symptoms, conditions=conditions)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Обработка формы и вывод результатов"""
    global ontology_data
    
    selected_symptoms = request.form.getlist('symptoms')
    selected_conditions = request.form.getlist('conditions')
    
    print(f"\n" + "="*50)
    print(f"USER SELECTION:")
    print(f"Symptoms: {selected_symptoms}")
    print(f"Conditions: {selected_conditions}")
    print("="*50)

    if ontology_data is None:
        ontology_data = get_all_entities_directly()
    
    programs = recommend_programs_smart(selected_symptoms, selected_conditions, ontology_data)
    
    print(f"\nFINAL: Found {len(programs)} recommended programs")

    return render_template('results.html', 
                         programs=programs,
                         selected_symptoms=selected_symptoms,
                         selected_conditions=selected_conditions)

@app.route('/debug_all')
def debug_all():
    """Полная отладка всей онтологии"""
    global ontology_data
    
    if ontology_data is None:
        ontology_data = get_all_entities_directly()
    
    return {
        'symptoms': ontology_data['symptoms'],
        'conditions': ontology_data['conditions'],
        'programs': [
            {
                'name': p['name'],
                'methods': p['methods'],
                'recommendations': p['recommendations'],
                'contraindications': p['contraindications']
            }
            for p in ontology_data['programs']
        ]
    }

if __name__ == '__main__':
    app.run(debug=True)