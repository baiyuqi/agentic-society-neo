from asociety.repository.database import get_engine
from asociety.repository.experiment_rep import QuestionAnswer
from asociety.repository.persona_rep import Persona



def __parseChoice(text):
    if(text == None):
       print("没有获得回答，返回1")
       return 1
    import re
    pattern = r"\*\*(\d+):|\[(\d+)\]|\*\*(\d+)\*\*|\[nchoice\]: (\d+)"

    match = re.search(pattern, text)

    if match:
        # 因为用了两个捕获组，可能只匹配到其中一个
        number = next(g for g in match.groups() if g)

        return int(number)
    else:
        print("匹配失败，返回1")
        print(text)
        return 1
def __ipipanswers_of(persona_id):
    from asociety.personality.answer_extractor import get_answers
    return get_answers(persona_id)

def __parse_personality(pobj):

    def _parse_one(personality,  name, data):
        first = name.upper()[0]
        setattr(personality, name,  data[first])
        setattr(personality, name + '_score',  data['score'])
        traits = data['traits']
        for t in traits:
            ks = t.keys()
            tname = list(ks)[1]
            tvalue = t[tname]
            tscore = t['score']
            setattr(personality, tname, tvalue)
            tscore_name = tname + '_score'
            setattr(personality, tscore_name, tscore)
    from asociety.repository.personality_rep import Personality
    ps = pobj['person']['result']['personalities']
    personality = Personality()
    personality.theory = pobj['theory']
    personality.model = pobj['model']
    personality.question = pobj['question']
    import json
    pjson = json.dumps(pobj)
    personality.personality_json = pjson

    for p in ps:
        for key in p.keys():
            
            v = p[key]
            _parse_one(personality,key,v)
    return personality


def personality_by(pid, sex, age, answers):
 
        if sex == 'Male' or sex == 'M':
            sex = 'M'
        else:
            sex = 'F'
        from asociety.personality.ipipneo import IpipNeo
        result = IpipNeo(120,test=True).compute(
                    sex=sex, age=age, answers={"answers": answers}, compare=True
                )
        p = __parse_personality(result)
        p.persona_id = pid
       

        
        from asociety.personality.ipipneo.quiz import plot_results
        #plot_results(result=result)
        return p
def personality_of(pid):
        
        from sqlalchemy.orm import Session
        with Session(get_engine()) as session:
            persona = session.get(Persona,pid)
        rst = __ipipanswers_of(pid)
        from asociety.personality.ipipneo import IpipNeo

        if persona.sex == 'Male':
            sex = 'M'
        else:
            sex = 'F'

        result = IpipNeo(120).compute(
                    sex=sex, age=persona.age, answers={"answers": rst}, compare=True
                )
        p = __parse_personality(result)
        p.persona_id = persona.id
       

        
        from asociety.personality.ipipneo.quiz import plot_results
        #plot_results(result=result)
        return p
def extract():
       
    from sqlalchemy.orm import Session
    from tqdm import tqdm
    with Session(get_engine()) as session:
        ps = session.query(Persona.id).all()

    personalities = []
    for persona in tqdm(ps, desc="Extracting personalities"):
         try:
            pid = persona[0]
            p = personality_of(pid)
            personalities.append(p)
         except Exception as e:
            print(f"Error extracting personality for persona_id {pid}: {e}")
    return personalities
def plot_peronality(pid):
    from sqlalchemy.orm import Session
    from asociety.repository.personality_rep import Personality
    with Session(get_engine()) as session:
        ps = session.get(Personality, pid)
        from asociety.personality.ipipneo.quiz import plot_results
        import json
        per = json.loads(ps.personality_json)
        plot_results(result=per)

if __name__ == "__main__": 
    personality_of(491)
    #ps = extract('personality-2-exp')
    #savePersonalities(ps)
