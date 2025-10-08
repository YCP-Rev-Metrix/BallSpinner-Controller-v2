

/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick
import QtQuick.Controls
import QTDesignTest
import QtQuick3D 6.8
import Generated.Bundles.Materials
import Generated.Bundles.Effects

Page {
    id: screen01
    width: Constants.width
    height: Constants.height
    property alias buttonMotorPage: buttonMotorPage
    Rectangle {
        id: rectangle
        width: Constants.width
        height: Constants.height

        color: Constants.backgroundColor
        property alias sphereEulerRotationy: sphere.eulerRotation.y

        Button {
            id: button
            text: qsTr("Press me")
            anchors.verticalCenter: parent.verticalCenter
            icon.color: "#052a50"
            checkable: true
            anchors.horizontalCenter: parent.horizontalCenter

            Connections {
                target: button
                onClicked: animation.start()
            }
        }

        Text {
            id: label
            text: qsTr("Hello QTDesignTest")
            anchors.top: button.bottom
            font.family: Constants.font.family
            anchors.topMargin: 45
            anchors.horizontalCenter: parent.horizontalCenter

            SequentialAnimation {
                id: animation

                ColorAnimation {
                    id: colorAnimation1
                    target: rectangle
                    property: "color"
                    to: "#2294c6"
                    from: Constants.backgroundColor
                }

                ColorAnimation {
                    id: colorAnimation2
                    target: rectangle
                    property: "color"
                    easing.bezierCurve: [0.2, 0.2, 0.888, 0.0185, 1, 1]
                    running: true
                    to: Constants.backgroundColor
                    from: "#2294c6"
                }
            }
        }

        View3D {
            id: bowlingBallSimulation3DView
            x: 272
            y: 312
            width: 400
            height: 400
            environment: sceneEnvironment
            SceneEnvironment {
                id: sceneEnvironment
                antialiasingQuality: SceneEnvironment.High
                antialiasingMode: SceneEnvironment.MSAA
            }

            Node {
                id: scene
                DirectionalLight {
                    id: directionalLight
                }

                PerspectiveCamera {
                    id: sceneCamera
                    z: 350
                }

                Model {
                    id: sphere
                    source: "#Sphere"
                    eulerRotation.y: 0
                    eulerRotation.x: 12
                    materials: aluminium

                    NumberAnimation {
                        id: rotationAnimationSpin
                        target: sphere
                        property: "eulerRotation.y"
                        easing.bezierCurve: [0.2, 0.2, 0.8, 0.8, 1, 1]
                        paused: false
                        running: true
                        from: 0
                        to: 360
                        duration: 3000
                        loops: Animation.Infinite
                    }

                    ShockwaveEffect {
                        id: shockwaveEffect
                        x: 0
                        y: 0
                        time: 0
                        z: 0
                    }
                }
            }
        }

        Component {
            id: component3D
            Node {
                id: componentRoot2
            }
        }

        Component {
            id: component2
            Item {
                id: componentRoot1
                width: 100
                height: 100
            }
        }

        Component {
            id: component1
            Item {
                id: componentRoot
                width: 100
                height: 100
            }
        }

        Item {
            id: __materialLibrary__

            PrincipledMaterial {
                id: principledMaterial
                objectName: "New Material"
            }

            AluminiumMaterial {
                id: aluminium
                objectName: "Aluminium"
            }
        }

        SwipeView {
            id: swipeView
            x: 1490
            y: 234
            width: 200
            height: 200

            View3D {
                id: bowlingBallSimulation3DView1
                x: 260
                y: 300
                width: 400
                height: 400
                environment: sceneEnvironment1
                SceneEnvironment {
                    id: sceneEnvironment1
                    antialiasingQuality: SceneEnvironment.High
                    antialiasingMode: SceneEnvironment.MSAA
                }

                Node {
                    id: scene1
                    DirectionalLight {
                        id: directionalLight1
                    }

                    PerspectiveCamera {
                        id: sceneCamera1
                        z: 350
                    }

                    Model {
                        id: sphere1
                        source: "#Sphere"
                        materials: aluminium
                        eulerRotation.y: 0
                        eulerRotation.x: 12
                        NumberAnimation {
                            id: rotationAnimationSpin1
                            target: sphere1
                            property: "eulerRotation.y"
                            running: true
                            paused: false
                            loops: Animation.Infinite
                            easing.bezierCurve: [0.2, 0.2, 0.8, 0.8, 1, 1]
                            duration: 3000
                            to: 360
                            from: 0
                        }

                        ShockwaveEffect {
                            id: shockwaveEffect1
                            x: 0
                            y: 0
                            z: 0
                            time: 0
                        }
                    }
                }
            }

            View3D {
                id: bowlingBallSimulation3DView2
                x: -1230
                y: 66
                width: 400
                height: 400
                environment: sceneEnvironment2
                SceneEnvironment {
                    id: sceneEnvironment2
                    antialiasingQuality: SceneEnvironment.High
                    antialiasingMode: SceneEnvironment.MSAA
                }

                Node {
                    id: scene2
                    DirectionalLight {
                        id: directionalLight2
                    }

                    PerspectiveCamera {
                        id: sceneCamera2
                        z: 350
                    }

                    Model {
                        id: sphere2
                        source: "#Sphere"
                        materials: aluminium
                        eulerRotation.y: 0
                        eulerRotation.x: 12
                        NumberAnimation {
                            id: rotationAnimationSpin2
                            target: sphere2
                            property: "eulerRotation.y"
                            running: true
                            paused: false
                            loops: Animation.Infinite
                            easing.bezierCurve: [0.2, 0.2, 0.8, 0.8, 1, 1]
                            duration: 3000
                            to: 360
                            from: 0
                        }

                        ShockwaveEffect {
                            id: shockwaveEffect2
                            x: 0
                            y: 0
                            z: 0
                            time: 0
                        }
                    }
                }
            }

            View3D {
                id: bowlingBallSimulation3DView3
                x: -1230
                y: 66
                width: 400
                height: 400
                environment: sceneEnvironment3
                SceneEnvironment {
                    id: sceneEnvironment3
                    antialiasingQuality: SceneEnvironment.High
                    antialiasingMode: SceneEnvironment.MSAA
                }

                Node {
                    id: scene3
                    DirectionalLight {
                        id: directionalLight3
                    }

                    PerspectiveCamera {
                        id: sceneCamera3
                        z: 350
                    }

                    Model {
                        id: sphere3
                        source: "#Sphere"
                        materials: aluminium
                        eulerRotation.y: 0
                        eulerRotation.x: 12
                        NumberAnimation {
                            id: rotationAnimationSpin3
                            target: sphere3
                            property: "eulerRotation.y"
                            running: true
                            paused: false
                            loops: Animation.Infinite
                            easing.bezierCurve: [0.2, 0.2, 0.8, 0.8, 1, 1]
                            duration: 3000
                            to: 360
                            from: 0
                        }

                        ShockwaveEffect {
                            id: shockwaveEffect3
                            x: 0
                            y: 0
                            z: 0
                            time: 0
                        }
                    }
                }
            }
        }

        Button {
            id: buttonMotorPage
            x: 1333
            y: 862
            text: qsTr("TestMotorPage")
        }
    }
    states: [
        State {
            name: "clicked"
            when: button.checked

            PropertyChanges {
                target: label
                text: qsTr("Button Checked")
            }
        }
    ]
}

/*##^##
Designer {
    D{i:0;matPrevEnvDoc:"SkyBox";matPrevEnvValueDoc:"preview_studio";matPrevModelDoc:"#Sphere"}
D{i:10;cameraSpeed3d:25;cameraSpeed3dMultiplier:1}D{i:44;cameraSpeed3d:25;cameraSpeed3dMultiplier:1}
}
##^##*/

