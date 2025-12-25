from sqlalchemy.orm import Session
from models import PresetWord


def add_initial_presets(engine):
    with Session(engine) as session:
        if session.query(PresetWord).count() == 0:
            presets = [
                PresetWord(word='hello', translation='привет', category='Basic'),
                PresetWord(word='goodbye', translation='до свидания', category='Basic'),
                PresetWord(word='please', translation='пожалуйста', category='Basic'),
                PresetWord(word='thank you', translation='спасибо', category='Basic'),
                PresetWord(word='yes', translation='да', category='Basic'),
                PresetWord(word='no', translation='нет', category='Basic'),
                PresetWord(word='excuse me', translation='извините', category='Basic'),
                PresetWord(word='sorry', translation='простите', category='Basic'),
                PresetWord(word='help', translation='помогите', category='Basic'),
                PresetWord(word='bathroom', translation='туалет', category='Basic'),
                PresetWord(word='how much', translation='сколько стоит', category='Basic'),
                PresetWord(word='where', translation='где', category='Basic'),
                PresetWord(word='when', translation='когда', category='Basic'),
                PresetWord(word='who', translation='кто', category='Basic'),
                PresetWord(word='what', translation='что', category='Basic'),
                PresetWord(word='how', translation='как', category='Basic'),
                PresetWord(word='I don’t understand', translation='я не понимаю', category='Basic'),
                PresetWord(word='repeat, please', translation='повторите, пожалуйста', category='Basic'),
                PresetWord(word='good morning', translation='доброе утро', category='Basic'),
                PresetWord(word='good night', translation='спокойной ночи', category='Basic'),

                PresetWord(word='water', translation='вода', category='Food & Drink'),
                PresetWord(word='bread', translation='хлеб', category='Food & Drink'),
                PresetWord(word='milk', translation='молоко', category='Food & Drink'),
                PresetWord(word='tea', translation='чай', category='Food & Drink'),
                PresetWord(word='coffee', translation='кофе', category='Food & Drink'),
                PresetWord(word='sugar', translation='сахар', category='Food & Drink'),
                PresetWord(word='salt', translation='соль', category='Food & Drink'),
                PresetWord(word='apple', translation='яблоко', category='Food & Drink'),
                PresetWord(word='banana', translation='банан', category='Food & Drink'),
                PresetWord(word='orange', translation='апельсин', category='Food & Drink'),
                PresetWord(word='meat', translation='мясо', category='Food & Drink'),
                PresetWord(word='chicken', translation='курица', category='Food & Drink'),
                PresetWord(word='fish', translation='рыба', category='Food & Drink'),
                PresetWord(word='rice', translation='рис', category='Food & Drink'),
                PresetWord(word='soup', translation='суп', category='Food & Drink'),
                PresetWord(word='cheese', translation='сыр', category='Food & Drink'),
                PresetWord(word='egg', translation='яйцо', category='Food & Drink'),
                PresetWord(word='salad', translation='салат', category='Food & Drink'),
                PresetWord(word='butter', translation='масло', category='Food & Drink'),
                PresetWord(word='vegetables', translation='овощи', category='Food & Drink')
            ]
            session.add_all(presets)
            session.commit()
            print("Базовые сборники добавлены!")
