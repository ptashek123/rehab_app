document.addEventListener('DOMContentLoaded', function () {
    const patientForm = document.getElementById('patientForm');
    if (patientForm) {
        patientForm.addEventListener('submit', function (e) {
            const diagnosis = document.querySelector('select[name="diagnosis"]').value;
            const severity = document.querySelector('select[name="severity"]').value;
            const ageGroup = document.querySelector('select[name="age_group"]').value;
            const movementImpairment = document.querySelector('select[name="movement_impairment"]').value;
            const target = document.querySelector('select[name="target"]').value;

            if (!diagnosis || !severity || !ageGroup || !movementImpairment || !target) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля');
                return false;
            }
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    const severitySelect = document.querySelector('select[name="severity"]');
    if (severitySelect) {
        severitySelect.addEventListener('change', function () {
            console.log('Selected severity:', this.value);
        });
    }
});

async function findProgramsAPI(patientData) {
    try {
        const response = await fetch('/api/find-program', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(patientData)
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching programs:', error);
        return null;
    }
}

async function getAllProgramsAPI() {
    try {
        const response = await fetch('/api/programs');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching all programs:', error);
        return null;
    }
}