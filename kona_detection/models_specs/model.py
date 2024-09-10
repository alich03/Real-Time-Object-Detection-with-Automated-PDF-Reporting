from roboflow import Roboflow


def mymodel(frame1):
    
    api_key = "9YTRvYKXQ1Ao0pYl3o07"
    rf = Roboflow(api_key=api_key)
    project = rf.workspace().project("kona_2.11")
    model = project.version(1823).model

    # infer on a local image
    results=model.predict(frame1, confidence=0.100, overlap=0.10).json()

    return results