import datetime

class SessionData:
    def __init__(self, id: int,timeStamp: datetime.datetime, name: str, isShotMode: bool):

        if id is None:
            self.id = -1
        else:
            self.id = id

        self.timeStamp = timeStamp
        self.name = name
        self.isShotMode = isShotMode

    def get_id(self):
        return self.id

    def get_time_stamp(self):
        return self.timeStamp

    def get_name(self):
        return self.name

    def get_is_shot_mode(self):
        return self.isShotMode

    def __str__(self):
        return f"SessionData(id={self.id}, timeStamp={self.timeStamp}, name={self.name}, isShotMode={self.isShotMode})"