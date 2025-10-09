Feature: UI interactions and feedback (template)

  Scenario: User selects an option and triggers processing
    Given the user is on the configuration panel
    And a default option is selected
    When the user clicks the "Start" button
    Then a loading indicator is shown
    And upon completion the result card updates with computed values

  Scenario: User changes an option and sees updated expectation
    Given the user previously saw a result
    When the user selects a different option
    Then the selection control reflects the change
    And the expectation text updates accordingly

