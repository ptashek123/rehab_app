from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owl").load()

def get_all_subclasses(cls):
    """Безопасное получение всех подклассов"""
    try:
        return cls.subclasses()
    except:
        return []

def get_all_instances(cls):
    """Безопасное получение всех экземпляров"""
    try:
        return cls.instances()
    except:
        return []

def recommend_programs(selected_symptoms, selected_conditions):
    """
    Функция для подбора программ на основе симптомов и состояний.
    """
    recommended_programs = []

    symptom_objs = []
    for symptom_name in selected_symptoms:
        obj = onto.search_one(iri="*%s" % symptom_name)
        if not obj:
            obj = onto.search_one(label=symptom_name)
        if obj:
            symptom_objs.append(obj)
    
    condition_objs = []
    for condition_name in selected_conditions:
        obj = onto.search_one(iri="*%s" % condition_name)
        if not obj:
            obj = onto.search_one(label=condition_name)
        if obj:
            condition_objs.append(obj)

    all_programs = []
    for program_class in get_all_subclasses(onto.RehabProgram):
        all_programs.extend(get_all_instances(program_class))
    all_programs.extend(get_all_instances(onto.RehabProgram))

    for program in all_programs:
        if not program:
            continue
            
        # Критерий 1: Программа рекомендована для выбранных условий
        is_recommended = False
        try:
            recommendations = list(program.isRecommendedFor)
            for rec in recommendations:
                if rec in condition_objs or rec in symptom_objs:
                    is_recommended = True
                    break
        except:
            pass

        # Критерий 2: Нет противопоказаний
        has_contraindication = False
        try:
            contraindications = list(program.hasContraindication)
            for contra in contraindications:
                if contra in condition_objs or contra in symptom_objs:
                    has_contraindication = True
                    break
        except:
            pass

        if is_recommended and not has_contraindication:
            methods = []
            try:
                methods = [m.name for m in program.includesMethod]
            except:
                pass
                
            recommended_programs.append({
                'name': program.name,
                'methods': methods
            })

    return recommended_programs

@app.route('/')
def index():
    """Главная страница с формой выбора."""
    try:
        all_symptoms = []
        symptom_classes = list(get_all_subclasses(onto.Symptom))
        for cls in symptom_classes:
            all_symptoms.append(cls.name)
            all_symptoms.extend([ind.name for ind in get_all_instances(cls)])
        
        all_symptoms.extend([ind.name for ind in get_all_instances(onto.Symptom)])
        
        all_conditions = []
        condition_classes = list(get_all_subclasses(onto.MedicalCondition))
        for cls in condition_classes:
            all_conditions.append(cls.name)
            all_conditions.extend([ind.name for ind in get_all_instances(cls)])
        
        all_conditions.extend([ind.name for ind in get_all_instances(onto.MedicalCondition)])

        all_symptoms = list(set([s for s in all_symptoms if s]))
        all_conditions = list(set([c for c in all_conditions if c]))

    except Exception as e:
        print(f"Error loading ontology data: {e}")
        all_symptoms = ["Pain", "LimitedMobility", "MuscleWeakness"]
        all_conditions = ["Stroke", "SpinalInjury", "JointInjury"]

    return render_template('index.html', symptoms=all_symptoms, conditions=all_conditions)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Обработка формы и вывод результатов."""
    selected_symptoms = request.form.getlist('symptoms')
    selected_conditions = request.form.getlist('conditions')

    programs = recommend_programs(selected_symptoms, selected_conditions)

    return render_template('results.html', 
                           programs=programs, 
                           selected_symptoms=selected_symptoms, 
                           selected_conditions=selected_conditions)

if __name__ == '__main__':
    app.run(debug=True)