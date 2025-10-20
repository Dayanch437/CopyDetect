original_text = """
Ýaňy-ýakynda emeli aň tehnologiýalary dünýäde örän çalt ösýär. Köp ýurtlar bu ugurda täze taslamalary amala aşyrýarlar. Emeli aň adamlaryň gündelik işlerinde kömek edýär, maglumatlary çalt seljerýär we täze çözgütleri teklip edýär. Geljekde bu tehnologiýanyň bilim, saglygy goraýyş we ykdysadyýet ýaly ugurlarda möhüm orny boljakdygy aýdylýar.
"""
suspect_text = "Häzirki wagtda emeli aň ulgamlary dünýäniň köp ýurtlarynda güýçli depginde ösüş tapýar. Döwletler bu tehnologiýany ösdürmek üçin dürli taslamalary ýerine ýetirýärler. Emeli aň adamlaryň işini ýeňilleşdirýär, maglumatlary tiz analiz edýär we täze mümkinçilikleri hödürleýär. Geljekde bu tehnologiýa bilimde, saglygy goraýyşda hem-de ykdysadyýetde möhüm ähmiýete eýe bolar diýip çak edilýär"

def check_authorship(original_text, suspect_text):
    from google import genai
    client = genai.Client(api_key="AIzaSyACJRBaLcEj9eUliyb8dt292S8Nz66ve30")
    system_instruction = (
     "You are an authorship checker for Turkmen language. "
    "You will receive two Turkmen texts: one is the original, the other may be fake or plagiarized. "
    "Compare the two texts and say if the second text is written by the same author as the first, or if it is plagiarized. "
    "Explain your reasoning briefly."
    "Show some statistics about the texts, such as word choice, sentence structure, and style."
    "Please provide all responses in Turkmen language."
    )
    chat = client.chats.create(
    model="gemini-2.5-flash",
    )
    message = (
    f"{system_instruction}\n\n"
    f"Original: {original_text}\n"
    f"Suspect: {suspect_text}\n"
    "Is the suspect text plagiarized or written by the same author? Provide your answer in Turkmen."
    )

    response = chat.send_message(message)
    return response.text