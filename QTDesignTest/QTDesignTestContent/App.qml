import QtQuick
import QTDesignTest

Window {
    width: mainScreen.width
    height: mainScreen.height

    visible: true
    title: "QTDesignTest"

    Screen01Form {
        id: mainScreen
        buttonMotorPage.onClicked:{
            console.log("Hello Worlds!")
            stackView.push(MotorTest )
        }
    }

}

