class SnippetsFeature < Spinach::FeatureSteps
  include SharedAuthentication
  include SharedPaths
  include SharedProject
  include SharedSnippet

  Given 'I click link "Personal snippet one"' do
    click_link "Personal snippet one"
  end

  And 'I should not see "Personal snippet one" in snippets' do
    page.should_not have_content "Personal snippet one"
  end

  And 'I click link "Edit"' do
    within ".file_title" do
      click_link "Edit"
    end
  end

  And 'I click link "Destroy"' do
    click_link "Destroy"
  end

  And 'I submit new snippet "Personal snippet three"' do
    fill_in "personal_snippet_title", :with => "Personal snippet three"
    select "forever", :from => "personal_snippet_expires_at"
    fill_in "personal_snippet_file_name", :with => "my_snippet.rb"
    within('.file-editor') do
      find(:xpath, "//input[@id='personal_snippet_content']").set 'Content of snippet three'
    end
    click_button "Save"
  end

  Then 'I should see snippet "Personal snippet three"' do
    page.should have_content "Personal snippet three"
    page.should have_content "Content of snippet three"
  end

  And 'I submit new title "Personal snippet new title"' do
    fill_in "personal_snippet_title", :with => "Personal snippet new title"
    click_button "Save"
  end

  Then 'I should see "Personal snippet new title"' do
    page.should have_content "Personal snippet new title"
  end

  And 'I uncheck "Private" checkbox' do
    find(:xpath, "//input[@id='personal_snippet_private']").set true
    click_button "Save"
  end

  Then 'I should see "Personal snippet one" public' do
    page.should have_no_xpath("//i[@class='public-snippet']")
  end

  And 'I visit snippet page "Personal snippet one"' do
    visit snippet_path(snippet)
  end

  def snippet
    @snippet ||= PersonalSnippet.find_by_title!("Personal snippet one")
  end
end
