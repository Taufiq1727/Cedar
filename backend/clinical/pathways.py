"""Clinical pathway definitions for the adaptive question engine.

Each pathway defines a structured set of questions for a specific chief complaint.
The engine uses these to track progress and determine next questions.
"""

PATHWAYS = {
    "chest_pain": {
        "name": "Chest Pain Assessment",
        "chief_complaint_keywords": ["chest pain", "chest tightness", "chest discomfort", "heart pain", "seene mein dard", "chhati mein dard"],
        "questions": [
            {"key": "onset", "text": "When did the chest pain start?", "text_hi": "छाती में दर्द कब शुरू हुआ?", "text_kn": "ಎದೆ ನೋವು ಯಾವಾಗ ಪ್ರಾರಂಭವಾಯಿತು?", "type": "text", "required": True},
            {"key": "duration", "text": "How long does the pain last each time?", "text_hi": "हर बार दर्द कितनी देर तक रहता है?", "text_kn": "ಪ್ರತಿ ಬಾರಿ ನೋವು ಎಷ್ಟು ಸಮಯ ಇರುತ್ತದೆ?", "type": "text", "required": True},
            {"key": "location", "text": "Where exactly do you feel the pain? (left side, center, right side, or all over)", "text_hi": "दर्द ठीक कहां महसूस होता है?", "text_kn": "ನೋವು ಎಲ್ಲಿ ಇದೆ?", "type": "text", "required": True},
            {"key": "severity", "text": "On a scale of 1 to 10, how severe is the pain?", "text_hi": "1 से 10 के पैमाने पर दर्द कितना तेज़ है?", "text_kn": "1 ರಿಂದ 10 ರ ಪ್ರಮಾಣದಲ್ಲಿ ನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?", "type": "scale", "required": True},
            {"key": "character", "text": "What does the pain feel like? (sharp, dull, burning, pressure, squeezing)", "text_hi": "दर्द कैसा है? (तेज़, हल्का, जलन, दबाव)", "text_kn": "ನೋವು ಹೇಗಿದೆ?", "type": "select", "options": ["Sharp", "Dull", "Burning", "Pressure/Squeezing", "Stabbing", "Other"], "required": True},
            {"key": "radiation", "text": "Does the pain spread to your arm, jaw, neck, or back?", "text_hi": "क्या दर्द बांह, जबड़े, गर्दन या पीठ में फैलता है?", "text_kn": "ನೋವು ತೋಳು, ದವಡೆ, ಕುತ್ತಿಗೆ ಅಥವಾ ಬೆನ್ನಿಗೆ ಹರಡುತ್ತದೆಯೇ?", "type": "text", "required": True},
            {"key": "aggravating_factors", "text": "What makes the pain worse? (exertion, breathing, eating, lying down)", "text_hi": "दर्द किससे बढ़ता है?", "text_kn": "ನೋವು ಯಾವಾಗ ಹೆಚ್ಚಾಗುತ್ತದೆ?", "type": "text", "required": False},
            {"key": "relieving_factors", "text": "What makes the pain better? (rest, medication, position change)", "text_hi": "दर्द किससे कम होता है?", "text_kn": "ನೋವು ಯಾವಾಗ ಕಡಿಮೆಯಾಗುತ್ತದೆ?", "type": "text", "required": False},
            {"key": "breathlessness", "text": "Do you experience breathlessness or difficulty breathing?", "text_hi": "क्या आपको सांस लेने में तकलीफ़ होती है?", "text_kn": "ನಿಮಗೆ ಉಸಿರಾಟದ ತೊಂದರೆ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No", "Sometimes"], "required": True},
            {"key": "sweating", "text": "Do you experience excessive sweating along with the pain?", "text_hi": "क्या दर्द के साथ अत्यधिक पसीना आता है?", "text_kn": "ನೋವಿನ ಜೊತೆಗೆ ಅತಿಯಾದ ಬೆವರು ಬರುತ್ತದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "dizziness", "text": "Do you feel dizzy or lightheaded?", "text_hi": "क्या आपको चक्कर आता है?", "text_kn": "ನಿಮಗೆ ತಲೆ ತಿರುಗುವಿಕೆ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No", "Sometimes"], "required": True},
            {"key": "nausea", "text": "Do you feel nauseous or have you vomited?", "text_hi": "क्या आपको मितली या उल्टी होती है?", "text_kn": "ನಿಮಗೆ ವಾಕರಿಕೆ ಅಥವಾ ವಾಂತಿ ಇದೆಯೇ?", "type": "select", "options": ["Yes - Nausea", "Yes - Vomiting", "No"], "required": False},
            {"key": "past_cardiac_history", "text": "Do you have any history of heart problems, high blood pressure, or diabetes?", "text_hi": "क्या आपको दिल की बीमारी, उच्च रक्तचाप या मधुमेह का इतिहास है?", "text_kn": "ನಿಮಗೆ ಹೃದಯ ಸಮಸ್ಯೆಗಳು, ಅಧಿಕ ರಕ್ತದೊತ್ತಡ ಅಥವಾ ಮಧುಮೇಹದ ಇತಿಹಾಸ ಇದೆಯೇ?", "type": "text", "required": True},
            {"key": "medications", "text": "Are you currently taking any medications?", "text_hi": "क्या आप वर्तमान में कोई दवा ले रहे हैं?", "text_kn": "ನೀವು ಪ್ರಸ್ತುತ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "smoking_history", "text": "Do you smoke or use tobacco?", "text_hi": "क्या आप धूम्रपान करते हैं या तंबाकू का उपयोग करते हैं?", "text_kn": "ನೀವು ಧೂಮಪಾನ ಅಥವಾ ತಂಬಾಕು ಬಳಸುತ್ತೀರಾ?", "type": "select", "options": ["Yes - Currently", "Yes - Previously", "No"], "required": False},
            {"key": "family_history", "text": "Does anyone in your family have heart disease?", "text_hi": "क्या आपके परिवार में किसी को दिल की बीमारी है?", "text_kn": "ನಿಮ್ಮ ಕುಟುಂಬದಲ್ಲಿ ಯಾರಿಗಾದರೂ ಹೃದ್ರೋಗ ಇದೆಯೇ?", "type": "text", "required": False},
            {"key": "allergies", "text": "Do you have any known allergies to medications?", "text_hi": "क्या आपको किसी दवा से एलर्जी है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ಔಷಧಿಗಳಿಗೆ ಅಲರ್ಜಿ ಇದೆಯೇ?", "type": "text", "required": False},
        ],
    },
    "fever": {
        "name": "Fever Assessment",
        "chief_complaint_keywords": ["fever", "temperature", "bukhar", "jwara", "taap"],
        "questions": [
            {"key": "onset", "text": "When did the fever start?", "text_hi": "बुखार कब शुरू हुआ?", "text_kn": "ಜ್ವರ ಯಾವಾಗ ಪ್ರಾರಂಭವಾಯಿತು?", "type": "text", "required": True},
            {"key": "temperature", "text": "What was the highest temperature you recorded? (in °F or °C)", "text_hi": "सबसे ज़्यादा तापमान कितना था?", "text_kn": "ನೀವು ದಾಖಲಿಸಿದ ಅತ್ಯಧಿಕ ತಾಪಮಾನ ಎಷ್ಟು?", "type": "text", "required": True},
            {"key": "pattern", "text": "Is the fever constant, or does it come and go?", "text_hi": "बुखार लगातार है या आता-जाता है?", "text_kn": "ಜ್ವರ ನಿರಂತರವಾಗಿದೆಯೇ ಅಥವಾ ಬಂದು ಹೋಗುತ್ತದೆಯೇ?", "type": "select", "options": ["Constant", "Comes and goes", "Only at night", "Only in evening"], "required": True},
            {"key": "chills", "text": "Do you experience chills or rigors (shaking)?", "text_hi": "क्या आपको ठंड लगती है या कंपकंपी होती है?", "text_kn": "ನಿಮಗೆ ಚಳಿ ಅಥವಾ ನಡುಕ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "cough", "text": "Do you have a cough?", "text_hi": "क्या आपको खांसी है?", "text_kn": "ನಿಮಗೆ ಕೆಮ್ಮು ಇದೆಯೇ?", "type": "select", "options": ["Yes - Dry", "Yes - With phlegm", "No"], "required": True},
            {"key": "sore_throat", "text": "Do you have a sore throat?", "text_hi": "क्या आपके गले में दर्द है?", "text_kn": "ನಿಮಗೆ ಗಂಟಲು ನೋವು ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "body_pain", "text": "Do you have body pain or joint pain?", "text_hi": "क्या आपको शरीर या जोड़ों में दर्द है?", "text_kn": "ನಿಮಗೆ ಮೈ ನೋವು ಅಥವಾ ಕೀಲು ನೋವು ಇದೆಯೇ?", "type": "select", "options": ["Yes - Body pain", "Yes - Joint pain", "Yes - Both", "No"], "required": True},
            {"key": "headache", "text": "Do you have a headache?", "text_hi": "क्या आपको सिरदर्द है?", "text_kn": "ನಿಮಗೆ ತಲೆನೋವು ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "rash", "text": "Have you noticed any rash or skin changes?", "text_hi": "क्या आपने कोई दाने या त्वचा में बदलाव देखा है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ದದ್ದು ಅಥವಾ ಚರ್ಮದ ಬದಲಾವಣೆಗಳು ಕಂಡಿವೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "nausea_vomiting", "text": "Do you have nausea, vomiting, or diarrhea?", "text_hi": "क्या आपको मितली, उल्टी या दस्त है?", "text_kn": "ನಿಮಗೆ ವಾಕರಿಕೆ, ವಾಂತಿ ಅಥವಾ ಭೇದಿ ಇದೆಯೇ?", "type": "select", "options": ["Nausea", "Vomiting", "Diarrhea", "Multiple", "None"], "required": True},
            {"key": "urinary_symptoms", "text": "Do you have burning urination or increased frequency?", "text_hi": "क्या पेशाब में जलन या बार-बार पेशाब आती है?", "text_kn": "ನಿಮಗೆ ಮೂತ್ರ ವಿಸರ್ಜನೆಯಲ್ಲಿ ಉರಿ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "travel_history", "text": "Have you traveled recently, especially to any endemic or rural area?", "text_hi": "क्या आपने हाल ही में कहीं यात्रा की है?", "text_kn": "ನೀವು ಇತ್ತೀಚೆಗೆ ಪ್ರಯಾಣ ಮಾಡಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "contact_history", "text": "Has anyone around you been sick recently?", "text_hi": "क्या आपके आसपास कोई हाल ही में बीमार हुआ है?", "text_kn": "ನಿಮ್ಮ ಸುತ್ತಮುತ್ತಲಿನ ಯಾರಾದರೂ ಇತ್ತೀಚೆಗೆ ಅನಾರೋಗ್ಯಕ್ಕೆ ಒಳಗಾಗಿದ್ದಾರೆಯೇ?", "type": "text", "required": False},
            {"key": "past_medical_history", "text": "Do you have any existing medical conditions?", "text_hi": "क्या आपको कोई पहले से बीमारी है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ಈಗಾಗಲೇ ಇರುವ ವೈದ್ಯಕೀಯ ಪರಿಸ್ಥಿತಿಗಳಿವೆಯೇ?", "type": "text", "required": False},
            {"key": "medications", "text": "Are you taking any medications currently?", "text_hi": "क्या आप अभी कोई दवा ले रहे हैं?", "text_kn": "ನೀವು ಪ್ರಸ್ತುತ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "allergies", "text": "Do you have any known allergies?", "text_hi": "क्या आपको किसी चीज़ से एलर्जी है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ತಿಳಿದಿರುವ ಅಲರ್ಜಿಗಳಿವೆಯೇ?", "type": "text", "required": False},
        ],
    },
    "headache": {
        "name": "Headache Assessment",
        "chief_complaint_keywords": ["headache", "head pain", "migraine", "sir dard", "talenoovu"],
        "questions": [
            {"key": "onset", "text": "When did the headache start?", "text_hi": "सिरदर्द कब शुरू हुआ?", "text_kn": "ತಲೆನೋವು ಯಾವಾಗ ಪ್ರಾರಂಭವಾಯಿತು?", "type": "text", "required": True},
            {"key": "location", "text": "Where exactly is the headache? (front, back, one side, all over)", "text_hi": "सिरदर्द कहां है?", "text_kn": "ತಲೆನೋವು ಎಲ್ಲಿ ಇದೆ?", "type": "text", "required": True},
            {"key": "severity", "text": "On a scale of 1 to 10, how severe is the headache?", "text_hi": "1 से 10 के पैमाने पर सिरदर्द कितना तेज़ है?", "text_kn": "1 ರಿಂದ 10 ರ ಪ್ರಮಾಣದಲ್ಲಿ ತಲೆನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?", "type": "scale", "required": True},
            {"key": "character", "text": "What does the headache feel like? (throbbing, constant, sharp, pressure)", "text_hi": "सिरदर्द कैसा है?", "text_kn": "ತಲೆನೋವು ಹೇಗಿದೆ?", "type": "select", "options": ["Throbbing", "Constant/Dull", "Sharp/Stabbing", "Pressure/Band-like", "Other"], "required": True},
            {"key": "visual_changes", "text": "Do you have any visual changes, blurriness, or flashing lights?", "text_hi": "क्या आंखों में कोई बदलाव, धुंधलापन या चमक है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ದೃಷ್ಟಿ ಬದಲಾವಣೆಗಳಿವೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "nausea", "text": "Do you feel nauseous or have you vomited?", "text_hi": "क्या मितली या उल्टी होती है?", "text_kn": "ನಿಮಗೆ ವಾಕರಿಕೆ ಇದೆಯೇ?", "type": "select", "options": ["Yes - Nausea", "Yes - Vomiting", "No"], "required": True},
            {"key": "neck_stiffness", "text": "Do you have neck stiffness or pain when bending your neck forward?", "text_hi": "क्या गर्दन में अकड़न है?", "text_kn": "ನಿಮಗೆ ಕುತ್ತಿಗೆ ಬಿಗಿತ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "fever", "text": "Do you have a fever?", "text_hi": "क्या बुखार है?", "text_kn": "ನಿಮಗೆ ಜ್ವರ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "photophobia", "text": "Does light bother you more than usual?", "text_hi": "क्या रोशनी से तकलीफ़ होती है?", "text_kn": "ಬೆಳಕು ಸಾಮಾನ್ಯಕ್ಕಿಂತ ಹೆಚ್ಚು ತೊಂದರೆ ಮಾಡುತ್ತದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "weakness", "text": "Do you have weakness in any limb or difficulty speaking?", "text_hi": "क्या किसी अंग में कमज़ोरी या बोलने में दिक्कत है?", "text_kn": "ನಿಮಗೆ ಯಾವುದೇ ಅಂಗದಲ್ಲಿ ದೌರ್ಬಲ್ಯ ಅಥವಾ ಮಾತನಾಡಲು ಕಷ್ಟವಿದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "recent_trauma", "text": "Have you had any recent head injury or trauma?", "text_hi": "क्या हाल ही में सिर पर चोट लगी है?", "text_kn": "ನಿಮಗೆ ಇತ್ತೀಚೆಗೆ ಯಾವುದೇ ತಲೆ ಗಾಯ ಆಗಿದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "past_medical_history", "text": "Do you have any existing medical conditions like high blood pressure or migraines?", "text_hi": "क्या आपको उच्च रक्तचाप या माइग्रेन जैसी कोई बीमारी है?", "text_kn": "ನಿಮಗೆ ಅಧಿಕ ರಕ್ತದೊತ್ತಡ ಅಥವಾ ಮೈಗ್ರೇನ್ ಇದೆಯೇ?", "type": "text", "required": False},
            {"key": "medications", "text": "Are you taking any medications?", "text_hi": "क्या आप कोई दवा ले रहे हैं?", "text_kn": "ನೀವು ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
        ],
    },
    "abdominal_pain": {
        "name": "Abdominal Pain Assessment",
        "chief_complaint_keywords": ["stomach pain", "abdominal pain", "belly pain", "pet dard", "pet mein dard", "hotte noovu"],
        "questions": [
            {"key": "onset", "text": "When did the abdominal pain start?", "text_hi": "पेट में दर्द कब शुरू हुआ?", "text_kn": "ಹೊಟ್ಟೆ ನೋವು ಯಾವಾಗ ಪ್ರಾರಂಭವಾಯಿತು?", "type": "text", "required": True},
            {"key": "location", "text": "Where in your abdomen is the pain? (upper, lower, left, right, center, all over)", "text_hi": "पेट में दर्द कहां है?", "text_kn": "ಹೊಟ್ಟೆಯಲ್ಲಿ ನೋವು ಎಲ್ಲಿ ಇದೆ?", "type": "text", "required": True},
            {"key": "severity", "text": "On a scale of 1 to 10, how severe is the pain?", "text_hi": "1 से 10 के पैमाने पर दर्द कितना तेज़ है?", "text_kn": "1 ರಿಂದ 10 ರ ಪ್ರಮಾಣದಲ್ಲಿ ನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?", "type": "scale", "required": True},
            {"key": "character", "text": "What does the pain feel like? (crampy, sharp, dull, burning, colicky)", "text_hi": "दर्द कैसा है?", "text_kn": "ನೋವು ಹೇಗಿದೆ?", "type": "select", "options": ["Crampy", "Sharp", "Dull/Aching", "Burning", "Colicky (comes in waves)", "Other"], "required": True},
            {"key": "nausea_vomiting", "text": "Do you have nausea or vomiting?", "text_hi": "क्या मितली या उल्टी है?", "text_kn": "ವಾಕರಿಕೆ ಅಥವಾ ವಾಂತಿ ಇದೆಯೇ?", "type": "select", "options": ["Yes - Nausea only", "Yes - Vomiting", "No"], "required": True},
            {"key": "bowel_changes", "text": "Have you noticed changes in bowel habits? (diarrhea, constipation, blood in stool)", "text_hi": "क्या पेट साफ़ होने में बदलाव है?", "text_kn": "ಮಲ ವಿಸರ್ಜನೆಯಲ್ಲಿ ಬದಲಾವಣೆ ಇದೆಯೇ?", "type": "select", "options": ["Diarrhea", "Constipation", "Blood in stool", "Normal", "Other"], "required": True},
            {"key": "appetite", "text": "How is your appetite?", "text_hi": "भूख कैसी है?", "text_kn": "ಹಸಿವು ಹೇಗಿದೆ?", "type": "select", "options": ["Normal", "Decreased", "No appetite", "Increased"], "required": True},
            {"key": "fever", "text": "Do you have a fever?", "text_hi": "क्या बुखार है?", "text_kn": "ಜ್ವರ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "bloating", "text": "Do you have bloating or gas?", "text_hi": "क्या पेट फूला हुआ है या गैस है?", "text_kn": "ಉಬ್ಬರ ಅಥವಾ ಗ್ಯಾಸ್ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "urinary_symptoms", "text": "Do you have any urinary symptoms like burning or increased frequency?", "text_hi": "क्या पेशाब में कोई तकलीफ है?", "text_kn": "ಮೂತ್ರ ವಿಸರ್ಜನೆಯಲ್ಲಿ ತೊಂದರೆ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "weight_loss", "text": "Have you experienced unintentional weight loss recently?", "text_hi": "क्या हाल ही में बिना कारण वज़न कम हुआ है?", "text_kn": "ಇತ್ತೀಚೆಗೆ ಉದ್ದೇಶವಿಲ್ಲದೆ ತೂಕ ಕಡಿಮೆಯಾಗಿದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "past_surgical_history", "text": "Have you had any previous abdominal surgeries?", "text_hi": "क्या पहले पेट का कोई ऑपरेशन हुआ है?", "text_kn": "ನಿಮಗೆ ಹಿಂದೆ ಹೊಟ್ಟೆಯ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಆಗಿದೆಯೇ?", "type": "text", "required": False},
            {"key": "medications", "text": "Are you taking any medications including pain killers?", "text_hi": "क्या आप कोई दवा ले रहे हैं?", "text_kn": "ನೀವು ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "allergies", "text": "Do you have any known allergies?", "text_hi": "क्या कोई एलर्जी है?", "text_kn": "ಅಲರ್ಜಿ ಇದೆಯೇ?", "type": "text", "required": False},
        ],
    },
    "cough_breathing": {
        "name": "Cough & Breathing Problems Assessment",
        "chief_complaint_keywords": ["cough", "breathing problem", "breathlessness", "shortness of breath", "wheezing", "khansi", "saans", "kemmu"],
        "questions": [
            {"key": "onset", "text": "When did the cough or breathing problem start?", "text_hi": "खांसी या सांस की तकलीफ कब शुरू हुई?", "text_kn": "ಕೆಮ್ಮು ಅಥವಾ ಉಸಿರಾಟದ ತೊಂದರೆ ಯಾವಾಗ ಪ್ರಾರಂಭವಾಯಿತು?", "type": "text", "required": True},
            {"key": "cough_type", "text": "Is the cough dry or do you produce phlegm/sputum?", "text_hi": "खांसी सूखी है या बलगम आता है?", "text_kn": "ಕೆಮ್ಮು ಒಣ ಕೆಮ್ಮೇ ಅಥವಾ ಕಫ ಬರುತ್ತದೆಯೇ?", "type": "select", "options": ["Dry cough", "With phlegm - White/Clear", "With phlegm - Yellow/Green", "With phlegm - Blood-tinged"], "required": True},
            {"key": "severity", "text": "On a scale of 1 to 10, how severe is your breathing difficulty?", "text_hi": "1 से 10 में सांस की तकलीफ कितनी है?", "text_kn": "ಉಸಿರಾಟದ ತೊಂದರೆ ಎಷ್ಟು ತೀವ್ರ?", "type": "scale", "required": True},
            {"key": "breathlessness", "text": "Do you feel short of breath? When does it occur?", "text_hi": "क्या सांस फूलती है? कब होती है?", "text_kn": "ಉಸಿರಾಟದ ತೊಂದರೆ ಇದೆಯೇ? ಯಾವಾಗ?", "type": "select", "options": ["At rest", "On walking", "On climbing stairs", "On exertion", "No breathlessness"], "required": True},
            {"key": "wheezing", "text": "Do you hear any wheezing or whistling sound when breathing?", "text_hi": "क्या सांस लेते समय सीटी जैसी आवाज़ आती है?", "text_kn": "ಉಸಿರಾಡುವಾಗ ಶಿಳ್ಳೆ ಶಬ್ದ ಕೇಳುತ್ತದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "hemoptysis", "text": "Have you coughed up blood?", "text_hi": "क्या खांसी में खून आया है?", "text_kn": "ಕೆಮ್ಮಿನಲ್ಲಿ ರಕ್ತ ಬಂದಿದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "fever", "text": "Do you have a fever?", "text_hi": "क्या बुखार है?", "text_kn": "ಜ್ವರ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "chest_pain", "text": "Do you have any chest pain?", "text_hi": "क्या छाती में दर्द है?", "text_kn": "ಎದೆ ನೋವು ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"key": "weight_loss", "text": "Have you lost weight unintentionally?", "text_hi": "क्या बिना कारण वज़न कम हुआ है?", "text_kn": "ತೂಕ ಕಡಿಮೆಯಾಗಿದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "night_sweats", "text": "Do you experience night sweats?", "text_hi": "क्या रात को पसीना आता है?", "text_kn": "ರಾತ್ರಿ ಬೆವರು ಬರುತ್ತದೆಯೇ?", "type": "select", "options": ["Yes", "No"], "required": False},
            {"key": "smoking_history", "text": "Do you smoke or use tobacco? If yes, for how long?", "text_hi": "क्या आप धूम्रपान करते हैं?", "text_kn": "ನೀವು ಧೂಮಪಾನ ಮಾಡುತ್ತೀರಾ?", "type": "text", "required": True},
            {"key": "asthma_copd", "text": "Do you have asthma, COPD, or any lung disease?", "text_hi": "क्या आपको दमा या फेफड़ों की बीमारी है?", "text_kn": "ನಿಮಗೆ ಆಸ್ತಮಾ ಅಥವಾ ಶ್ವಾಸಕೋಶ ರೋಗ ಇದೆಯೇ?", "type": "text", "required": True},
            {"key": "tb_contact", "text": "Have you been in contact with anyone diagnosed with tuberculosis (TB)?", "text_hi": "क्या आपका टीबी के मरीज़ से संपर्क रहा है?", "text_kn": "ಕ್ಷಯ ರೋಗಿಯೊಂದಿಗೆ ಸಂಪರ್ಕ ಇದೆಯೇ?", "type": "select", "options": ["Yes", "No", "Not sure"], "required": True},
            {"key": "medications", "text": "Are you taking any medications including inhalers?", "text_hi": "क्या आप कोई दवा या इनहेलर ले रहे हैं?", "text_kn": "ನೀವು ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "allergies", "text": "Do you have any known allergies?", "text_hi": "क्या कोई एलर्जी है?", "text_kn": "ಅಲರ್ಜಿ ಇದೆಯೇ?", "type": "text", "required": False},
        ],
    },
    "general": {
        "name": "General Assessment",
        "chief_complaint_keywords": [],
        "questions": [
            {"key": "main_problem", "text": "Can you describe your main health concern in detail?", "text_hi": "अपनी मुख्य स्वास्थ्य समस्या का विस्तार से वर्णन करें।", "text_kn": "ನಿಮ್ಮ ಮುಖ್ಯ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಯನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ.", "type": "text", "required": True},
            {"key": "duration", "text": "How long have you been experiencing this problem?", "text_hi": "यह समस्या कब से है?", "text_kn": "ಈ ಸಮಸ್ಯೆ ಎಷ್ಟು ಸಮಯದಿಂದ ಇದೆ?", "type": "text", "required": True},
            {"key": "severity", "text": "On a scale of 1 to 10, how severe is your problem?", "text_hi": "1 से 10 में यह समस्या कितनी गंभीर है?", "text_kn": "ಸಮಸ್ಯೆ ಎಷ್ಟು ತೀವ್ರ?", "type": "scale", "required": True},
            {"key": "previous_treatment", "text": "Have you received any treatment for this before?", "text_hi": "क्या इसके लिए पहले कोई इलाज हुआ है?", "text_kn": "ಈ ಹಿಂದೆ ಚಿಕಿತ್ಸೆ ಪಡೆದಿದ್ದೀರಾ?", "type": "text", "required": True},
            {"key": "past_medical_history", "text": "Do you have any existing medical conditions?", "text_hi": "क्या कोई पुरानी बीमारी है?", "text_kn": "ಹಿಂದಿನ ವೈದ್ಯಕೀಯ ಇತಿಹಾಸ ಇದೆಯೇ?", "type": "text", "required": True},
            {"key": "medications", "text": "Are you currently taking any medications?", "text_hi": "क्या अभी कोई दवा चल रही है?", "text_kn": "ಪ್ರಸ್ತುತ ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?", "type": "text", "required": False},
            {"key": "allergies", "text": "Do you have any known allergies?", "text_hi": "क्या कोई एलर्जी है?", "text_kn": "ಅಲರ್ಜಿ ಇದೆಯೇ?", "type": "text", "required": False},
            {"key": "family_history", "text": "Does anyone in your family have a similar condition?", "text_hi": "क्या परिवार में किसी को ऐसी समस्या है?", "text_kn": "ಕುಟುಂಬದಲ್ಲಿ ಇಂತಹ ಸಮಸ್ಯೆ ಇದೆಯೇ?", "type": "text", "required": False},
        ],
    },
}


def detect_pathway(text: str) -> str:
    """Detect which clinical pathway matches the patient's chief complaint."""
    text_lower = text.lower()
    for pathway_id, pathway in PATHWAYS.items():
        if pathway_id == "general":
            continue
        for keyword in pathway["chief_complaint_keywords"]:
            if keyword in text_lower:
                return pathway_id
    return "general"


def get_pathway(pathway_id: str) -> dict:
    """Get a clinical pathway by ID."""
    return PATHWAYS.get(pathway_id, PATHWAYS["general"])


def get_next_question(pathway_id: str, answered_keys: list, language: str = "en") -> dict | None:
    """Get the next unanswered question in the pathway."""
    pathway = get_pathway(pathway_id)
    for q in pathway["questions"]:
        if q["key"] not in answered_keys:
            lang_key = f"text_{language}" if language != "en" else "text"
            question_text = q.get(lang_key, q["text"])
            return {
                "question_key": q["key"],
                "question_text": question_text,
                "question_type": q.get("type", "text"),
                "options": q.get("options"),
                "required": q.get("required", False),
            }
    return None


def calculate_progress(pathway_id: str, answered_keys: list) -> int:
    """Calculate completion percentage for a pathway."""
    pathway = get_pathway(pathway_id)
    total = len(pathway["questions"])
    answered = len([k for k in answered_keys if any(q["key"] == k for q in pathway["questions"])])
    return min(int((answered / total) * 100), 100) if total > 0 else 100
