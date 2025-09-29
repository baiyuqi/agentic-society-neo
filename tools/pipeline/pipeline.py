from asociety.personality.qa_service import questionAnswerAll2, initializeQuestionAnswer
from asociety.repository.personality_rep import savePersonalities
from asociety.personality.personality_extractor import extract
if __name__ == "__main__":
    #generator:PersonaGenerator = PersonaGeneratorFactory.create()
    #print("Sampling personas...")
    #samples = generator.sampling(100)
    #print("Saving personas...")
    #savePersonas(samples)

    from asociety.config import configuration
    if configuration['request_method'] == 'question':
        
        print("Intializing question-answer table for all personas...")
        initializeQuestionAnswer()
        print("Answering questions for all personas...")
        questionAnswerAll2()
        
    else:
        from asociety.personality.quiz_service import create_tasks, execute_tasks
        print("Creating tasks for all personas...")
        create_tasks()
        print("Executing tasks for all personas...")
        execute_tasks()
    print("Extracting personalities...")
    ps = extract()
    print("Saving personalities...")
    savePersonalities(ps)
    print("Pipeline finished.")
