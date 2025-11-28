from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owx").load()

def safe_get_subclasses(cls):
    """Безопасное получение подклассов"""
    try:
        return list(cls.subclasses())
    except Exception as e:
        print(f"Error getting subclasses for {cls}: {e}")
        return []

def safe_get_instances(cls):
    """Безопасное получение экземпляров"""
    try:
        return list(cls.instances())
    except Exception as e:
        print(f"Error getting instances for {cls}: {e}")
        return []

def get_all_entities(class_name):
    """Получение всех сущностей класса (классов и индивидов)"""
    entities = []
    try:
        main_class = onto.search_one(iri=f"*{class_name}")
        if main_class:
            entities.append(main_class.name)
            for subclass in safe_get_subclasses(main_class):
                entities.append(subclass.name)
            for instance in safe_get_instances(main_class):
                if hasattr(instance, 'name') and instance.name:
                    entities.append(instance.name)
    except Exception as e:
        print(f"Error getting entities for {class_name}: {e}")
    
    return list(set(entities))

def recommend_programs(selected_symptoms, selected_conditions):
    """Подбор программ на основе симптомов и состояний"""
    recommended_programs = []

    try:
        all_programs = []
        rehab_class = onto.search_one(iri="*RehabProgram")
        if rehab_class:
            all_programs = safe_get_instances(rehab_class)
        
        print(f"Found {len(all_programs)} programs")

        for program in all_programs:
            if not program:
                continue
                
            program_info = {
                'name': program.name,
                'methods': [],
                'recommended_for': [],
                'contraindications': []
            }

            try:
                if hasattr(program, 'includesMethod'):
                    methods = list(program.includesMethod)
                    program_info['methods'] = [m.name for m in methods if hasattr(m, 'name')]
            except Exception as e:
                print(f"Error getting methods for {program.name}: {e}")

            is_recommended = False
            try:
                if hasattr(program, 'isRecommendedFor'):
                    recommendations = list(program.isRecommendedFor)
                    program_info['recommended_for'] = [r.name for r in recommendations if hasattr(r, 'name')]
                    
                    for rec in recommendations:
                        rec_name = getattr(rec, 'name', None)
                        if rec_name in selected_symptoms or rec_name in selected_conditions:
                            is_recommended = True
                            break
            except Exception as e:
                print(f"Error getting recommendations for {program.name}: {e}")

            has_contraindication = False
            try:
                if hasattr(program, 'hasContraindication'):
                    contraindications = list(program.hasContraindication)
                    program_info['contraindications'] = [c.name for c in contraindications if hasattr(c, 'name')]
                    
                    for contra in contraindications:
                        contra_name = getattr(contra, 'name', None)
                        if contra_name in selected_symptoms or contra_name in selected_conditions:
                            has_contraindication = True
                            break
            except Exception as e:
                print(f"Error getting contraindications for {program.name}: {e}")

            if is_recommended and not has_contraindication:
                recommended_programs.append(program_info)

    except Exception as e:
        print(f"Error in recommend_programs: {e}")

    return recommended_programs

@app.route('/')
def index():
    """Главная страница с формой выбора"""
    try:
        symptoms = get_all_entities("Symptom")
        conditions = get_all_entities("MedicalCondition")
        
        print(f"Loaded {len(symptoms)} symptoms and {len(conditions)} conditions")
        
    except Exception as e:
        print(f"Error loading ontology: {e}")
        symptoms = ["Боль", "ОграниченнаяПодвижность", "МышечнаяСлабость"]
        conditions = ["Инсульт", "ТравмаПозвоночника", "ТравмаСустава"]

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