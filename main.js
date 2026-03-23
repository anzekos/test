"use strict";

function OnNewShellUI(shellUI) {
    shellUI.Events.Register(
        Event_NewShellFrame,
        function(shellFrame) {
            shellFrame.Events.Register(
                Event_Started,
                function() {
                    try {
                        // 1. Ustvarimo nov zavihek (Tab) v desnem podoknu (Right Pane)
                        var aiTab = shellFrame.RightPane.AddTab("ai_chat_tab", "AI Pravni Asistent", "_last");
                        aiTab.ShowDashboard("ai_chat_dashboard", null);
                        aiTab.Visible = true;
                        
                        // 2. Dodamo še gumb v levi stranski meni (Task Pane) za izskakovno okno
                        var cmdOpenModal = shellUI.Commands.CreateCustomCommand("Odpri AI Asistenta (Okno)");
                        var myGroup = shellFrame.TaskPane.CreateGroup("AI Funkcije", 1);
                        shellFrame.TaskPane.AddCustomCommandToGroup(cmdOpenModal, myGroup, 0);
                        
                        shellUI.Events.Register(
                            Event_CustomCommand,
                            function(command) {
                                if (command === cmdOpenModal) {
                                    shellFrame.ShowDashboard("ai_chat_dashboard", null);
                                }
                            }
                        );
                    } catch (e) {
                        // M-Files handles the extension quietly if right pane isn't available
                    }
                }
            );
        }
    );
}
