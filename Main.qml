import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
// import QtGraphicalEffects

Window {
    id: root
    width: 640
    height: 480
    visible: true
    title: qsTr("Overengineered Hello")

    property bool clicked: false
    property color chillColor: clicked ? "#ffeaa7" : "#a29bfe"

    // Dramatic gradient background
    Rectangle {
        id: bg
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: chillColor }
            GradientStop { position: 1.0; color: "#74b9ff" }
        }

        Behavior on gradient {
            ColorAnimation { duration: 1200; easing.type: Easing.InOutQuad }
        }

        // Useless rotating circle in the background
        Rectangle {
            id: spinner
            width: 150; height: 150
            radius: width / 2
            color: "white"
            opacity: 0.1
            anchors.centerIn: parent
            RotationAnimator on rotation {
                from: 0; to: 360; duration: 6000; loops: Animation.Infinite
            }
        }
    }

    // Shadowed central card
    Rectangle {
        id: card
        width: 400
        height: 250
        anchors.centerIn: parent
        radius: 20
        color: "white"
        opacity: 0.95

        layer.enabled: true
        // layer.effect: DropShadow {
        //     radius: 12
        //     samples: 32
        //     color: "#40000000"
        //     horizontalOffset: 2
        //     verticalOffset: 4
        // }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16
            // horizontalAlignment: Qt.AlignHCenter
            // verticalAlignment: Qt.AlignVCenter

            Text {
                id: titleText
                text: root.clicked ? "You clicked it 😎" : "Hello there 👋"
                font.pixelSize: 28
                color: "#2d3436"
                Layout.alignment: Qt.AlignHCenter

                Behavior on text {
                    SequentialAnimation {
                        NumberAnimation { target: titleText; property: "scale"; from: 1; to: 1.2; duration: 150 }
                        NumberAnimation { target: titleText; property: "scale"; from: 1.2; to: 1; duration: 150 }
                    }
                }
            }

            Button {
                id: button
                text: root.clicked ? "Undo Chill" : "Click for Chill"
                Layout.alignment: Qt.AlignHCenter
                font.pixelSize: 18

                background: Rectangle {
                    implicitWidth: 150
                    implicitHeight: 40
                    radius: 8
                    gradient: Gradient {
                        GradientStop { position: 0; color: root.clicked ? "#fab1a0" : "#81ecec" }
                        GradientStop { position: 1; color: root.clicked ? "#ff7675" : "#00cec9" }
                    }
                }

                onClicked: {
                    root.clicked = !root.clicked
                    feedbackTimer.start()
                }
            }

            Text {
                id: feedbackText
                text: ""
                font.pixelSize: 18
                color: "#636e72"
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.0

                states: [
                    State {
                        name: "visible"
                        when: feedbackText.opacity > 0
                        PropertyChanges { target: feedbackText; color: "#0984e3" }
                    }
                ]
                transitions: Transition {
                    NumberAnimation { properties: "opacity"; duration: 300 }
                }
            }
            Text { text: backend.message }
            Button { text: "Call Python"; onClicked: backend.doSomething() }
        }
    }

    // Timer for unnecessary delayed text changes
    Timer {
        id: feedbackTimer
        interval: 1000
        onTriggered: {
            feedbackText.text = root.clicked ? "Much chill activated 🧘" : "Chill revoked 😤"
            feedbackText.opacity = 1.0
            hideTextTimer.start()
        }
    }

    Timer {
        id: hideTextTimer
        interval: 2500
        onTriggered: feedbackText.opacity = 0.0
    }

    // Pointless blinking border animation
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: Qt.rgba(Math.random(), Math.random(), Math.random(), 0.3)
        border.width: 4

        SequentialAnimation on border.color {
            loops: Animation.Infinite
            ColorAnimation { to: "lightpink"; duration: 800 }
            ColorAnimation { to: "lightblue"; duration: 800 }
            ColorAnimation { to: "lightgreen"; duration: 800 }
        }
    }
}
