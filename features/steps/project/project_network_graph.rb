class ProjectNetworkGraph < Spinach::FeatureSteps
  include SharedAuthentication
  include SharedProject

  Then 'page should have network graph' do
    page.should have_content "Project Network Graph"
    page.should have_selector ".graph"
  end

  When 'I visit project "Shop" network page' do
    # Stub Graph max_size to speed up test (10 commits vs. 650)
    Network::Graph.stub(max_count: 10)

    project = Project.find_by_name("Shop")
    visit project_graph_path(project, "master")
  end

  And 'page should select "master" in select box' do
    page.should have_selector '#ref_chzn span', text: "master"
  end

  And 'page should select "v2.1.0" in select box' do
    page.should have_selector '#ref_chzn span', text: "v2.1.0"
  end

  And 'page should have "master" on graph' do
    within '.graph' do
      page.should have_content 'master'
    end
  end

  When 'I switch ref to "stable"' do
    page.select 'stable', from: 'ref'
    sleep 2
  end

  When 'I switch ref to "v2.1.0"' do
    page.select 'v2.1.0', from: 'ref'
    sleep 2
  end

  When 'I switch ref to "v2.1.0"' do
    page.select 'v2.1.0', from: 'ref'
    sleep 2
  end

  When 'click "Show only selected branch" checkbox' do
    find('#filter_ref').click
    sleep 2
  end

  Then 'page should have content not cotaining "v2.1.0"' do
    within '.graph' do
      page.should have_content 'cleaning'
    end
  end

  Then 'page should not have content not cotaining "v2.1.0"' do
    within '.graph' do
      page.should_not have_content 'cleaning'
    end
  end

  And 'page should select "stable" in select box' do
    page.should have_selector '#ref_chzn span', text: "stable"
  end

  And 'page should select "v2.1.0" in select box' do
    page.should have_selector '#ref_chzn span', text: "v2.1.0"
  end

  And 'page should have "stable" on graph' do
    within '.graph' do
      page.should have_content 'stable'
    end
  end

  When 'I looking for a commit by SHA of "v2.1.0"' do
    within ".content .search" do
      fill_in 'q', with: '98d6492'
      find('button').click
    end
    sleep 2
  end

  And 'page should have "v2.1.0" on graph' do
    within '.graph' do
      page.should have_content 'v2.1.0'
    end
  end
end
