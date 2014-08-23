Feature: Admin Users
  Background:
    Given I sign in as an admin
    And system has users

  Scenario: On Admin Users
    Given I visit admin users page
    Then I should see all users

  Scenario: Edit user and change username to non ascii char
    When I visit admin users page
    And Click edit
    And Input non ascii char in username
    And Click save
    Then See username error message
    And Not chenged form action url
