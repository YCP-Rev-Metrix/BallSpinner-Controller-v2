

/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick
import QtQuick.Controls

Page {
    id: page
    height: Constants.height
    property alias labelSMotorRPMText: labelSMotorRPM.text
    width: Constants.width
    Rectangle {
        id: rectangle
        x: 145
        y: -76
        width: 1920
        height: 1080
        color: "#1c830a"
        topLeftRadius: 0
        transformOrigin: Item.Center

        Button {
            id: buttonIncreaseRPM
            x: 613
            y: 643
            width: 251
            height: 130
            text: qsTr("Increase Spin Motor RPM")
            icon.source: "../../../../Users/raven/Downloads/wizardddddd.png"
            display: AbstractButton.TextUnderIcon
        }

        Button {
            id: buttonDecreaseRPM
            x: 959
            y: 643
            width: 251
            height: 130
            text: qsTr("Increase Spin Motor RPM")
            icon.source: "../../../../Users/raven/Downloads/wizardddddd.png"
            display: AbstractButton.TextUnderIcon
        }

        Button {
            id: buttonToMain
            x: 35
            y: 927
            width: 251
            height: 130
            text: qsTr("Back To Main")
            icon.source: "../../../../Users/raven/Downloads/wizardddddd.png"
            display: AbstractButton.TextUnderIcon
        }

        Button {
            id: buttonEnableMotorSpin
            x: 468
            y: 236
            width: 251
            height: 130
            text: qsTr("Enable Spin Motor")
            icon.source: "../../../../Users/raven/Downloads/wizardddddd.png"
            display: AbstractButton.TextUnderIcon
        }

        Label {
            id: labelSMotorRPM
            x: 775
            y: 562
            width: 251
            height: 38
            text: qsTr("Assigned Motor RPM and Encoder RPM:")
        }
    }
}
