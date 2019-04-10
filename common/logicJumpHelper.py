def evaluateJumpRules(answer, jumpRules):
    for jumpRule in jumpRules:
        propertyName = jumpRule['propertyName']
        propertyValue = jumpRule['propertyValue']
        
        if propertyName not in answer:
            return (False, None)
            
        inputtedAnswer = answer[propertyName]
        if isinstance(inputtedAnswer, dict) and '_ref' in inputtedAnswer:
            inputtedAnswer = inputtedAnswer['_ref']

        isEqual = jumpRule['isEqual']
        if isEqual and inputtedAnswer == propertyValue or not isEqual and inputtedAnswer != propertyValue:
            return (True, jumpRule['jumpIndex'])

    return (False, None)


