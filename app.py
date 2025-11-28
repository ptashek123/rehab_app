from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owx").load()

def get_entity_by_label(label):
    """Найти сущность по метке (rdfs:label)"""
    return onto.search_one(label=label)

def get_all_entities_by_class_label(class_label):
    """Получить все сущности по метке класса"""
    entities = []
    try:
        target_class = get_entity_by_label(class_label)
        if target_class:
            for individual in target_class.instances():
                individual_label = individual.label.first() if individual.label else individual.name
                if individual_label:
                    entities.append(individual_label)
    except Exception as e:
        print(f"Error getting entities for {class_label}: {e}")
    
    return list(set(entities))

def get_all_classes_by_parent_label(parent_label):
    """Получить все подклассы по метке родительского класса"""
    classes = []
    try:
        parent_class = get_entity_by_label(parent_label)
        if parent_class:
            for subclass in parent_class.subclasses():
                subclass_label = subclass.label.first() if subclass.label else subclass.name
                if subclass_label:
                    classes.append(subclass_label)
    except Exception as e:
        print(f"Error getting subclasses for {parent_label}: {e}")
    
    return list(set(classes))

def recommend_programs(selected_symptoms, selected_conditions):
    """Подбор программ на основе симптомов и состояний"""
    recommended_programs = []

    try:
        rehab_class = get_entity_by_label("RehabProgram")
        if not rehab_class:
            print("RehabProgram class not found")
            return []
        
        all_programs = list(rehab_class.instances())
        print(f"Found {len(all_programs)} programs")

        recommended_prop = get_entity_by_label("isRecommendedFor")
        includes_prop = get_entity_by_label("includesMethod")
        contraindication_prop = get_entity_by_label("hasContraindication")

        for program in all_programs:
            if not program:
                continue
            
            program_label = program.label.first() if program.label else program.name
            if not program_label:
                continue

            program_info = {
                'name': program_label,
                'methods': [],
                'recommended_for': [],
                'contraindications': []
            }

            if includes_prop:
                try:
                    methods = getattr(program, includes_prop.name, [])
                    if not isinstance(methods, list):
                        methods = [methods]
                    for method in methods:
                        if method:
                            method_label = method.label.first() if method.label else method.name
                            if method_label:
                                program_info['methods'].append(method_label)
                except Exception as e:
                    print(f"Error getting methods for {program_label}: {e}")

            is_recommended = False
            if recommended_prop:
                try:
                    recommendations = getattr(program, recommended_prop.name, [])
                    if not isinstance(recommendations, list):
                        recommendations = [recommendations]
                    
                    for rec in recommendations:
                        if rec:
                            rec_label = rec.label.first() if rec.label else rec.name
                            program_info['recommended_for'].append(rec_label)
                            
                            if rec_label in selected_symptoms or rec_label in selected_conditions:
                                is_recommended = True
                except Exception as e:
                    print(f"Error getting recommendations for {program_label}: {e}")

            has_contraindication = False
            if contraindication_prop:
                try:
                    contraindications = getattr(program, contraindication_prop.name, [])
                    if not isinstance(contraindications, list):
                        contraindications = [contraindications]
                    
                    for contra in contraindications:
                        if contra:
                            contra_label = contra.label.first() if contra.label else contra.name
                            program_info['contraindications'].append(contra_label)
                            
                            if contra_label in selected_symptoms or contra_label in selected_conditions:
                                has_contraindication = True
                except Exception as e:
                    print(f"Error getting contraindications for {program_label}: {e}")

            if is_recommended and not has_contraindication:
                recommended_programs.append(program_info)

    except Exception as e:
        print(f"Error in recommend_programs: {e}")

    return recommended_programs

@app.route('/')
def index():
    """Главная страница с формой выбора"""
    try:
        symptoms = get_all_entities_by_class_label("Symptom")
        conditions = get_all_entities_by_class_label("MedicalCondition")
        
        if not symptoms:
            symptoms = get_all_classes_by_parent_label("Symptom")
        if not conditions:
            conditions = get_all_classes_by_parent_label("MedicalCondition")
        
        print(f"Loaded {len(symptoms)} symptoms: {symptoms}")
        print(f"Loaded {len(conditions)} conditions: {conditions}")
        
    except Exception as e:
        print(f"Error loading ontology: {e}")
        symptoms = ["Боль", "ОграниченнаяПодвижность", "МышечнаяСлабость", "НарушениеРечи", "Депрессия"]
        conditions = ["Инсульт", "ТравмаПозвоночника", "ТравмаСустава", "РассеянныйСклероз"]
    
    return render_template('index.html', symptoms=symptoms, conditions=conditions)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Обработка формы и вывод результатов"""
    selected_symptoms = request.form.getlist('symptoms')
    selected_conditions = request.form.getlist('conditions')
    
    print(f"Selected symptoms: {selected_symptoms}")
    print(f"Selected conditions: {selected_conditions}")

    programs = recommend_programs(selected_symptoms, selected_conditions)
    
    print(f"Found {len(programs)} recommended programs")

    return render_template('results.html', 
                         programs=programs,
                         selected_symptoms=selected_symptoms,
                         selected_conditions=selected_conditions)

if __name__ == '__main__':
    app.run(debug=True)