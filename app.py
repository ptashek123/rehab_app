from flask import Flask, render_template, request
from owlready2 import *

app = Flask(__name__)

onto = get_ontology("ontology/rehab_ontology.owl").load()

def recommend_programs(selected_symptoms, selected_conditions):
    """
    Функция для подбора программ на основе симптомов и состояний.
    """
    recommended_programs = []

    symptom_objs = []
    for symptom_name in selected_symptoms:
        obj = onto.search_one(iri="*%s" % symptom_name)
        if obj:
            symptom_objs.append(obj)
    
    condition_objs = []
    for condition_name in selected_conditions:
        obj = onto.search_one(iri="*%s" % condition_name)
        if obj:
            condition_objs.append(obj)

    all_programs = list(onto.RehabProgram.instances())

    for program in all_programs:
        # Критерий 1: Программа рекомендована для выбранных условий
        is_recommended = False
        recommendations = list(program.isRecommendedFor)
        for rec in recommendations:
            if rec in condition_objs or rec in symptom_objs:
                is_recommended = True
                break

        # Критерий 2: Нет противопоказаний
        has_contraindication = False
        contraindications = list(program.hasContraindication)
        for contra in contraindications:
            if contra in condition_objs or contra in symptom_objs:
                has_contraindication = True
                break

        if is_recommended and not has_contraindication:
            methods = [m.name for m in program.includesMethod]
            recommended_programs.append({
                'name': program.name,
                'methods': methods
            })

    return recommended_programs

@app.route('/')
def index():
    """Главная страница с формой выбора"""
    all_symptoms = [cls.name for cls in onto.Symptom.subclasses()] + [ind.name for ind in onto.Symptom.instances()]
    all_conditions = [cls.name for cls in onto.MedicalCondition.subclasses()] + [ind.name for ind in onto.MedicalCondition.instances()]

    all_symptoms = list(set([s for s in all_symptoms if s]))
    all_conditions = list(set([c for c in all_conditions if c]))

    return render_template('index.html', symptoms=all_symptoms, conditions=all_conditions)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Обработка формы и вывод результатов"""
    selected_symptoms = request.form.getlist('symptoms')
    selected_conditions = request.form.getlist('conditions')

    programs = recommend_programs(selected_symptoms, selected_conditions)

    return render_template('results.html', 
                           programs=programs, 
                           selected_symptoms=selected_symptoms, 
                           selected_conditions=selected_conditions)

if __name__ == '__main__':
    app.run(debug=True)