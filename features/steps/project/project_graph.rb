class ProjectGraph < Spinach::FeatureSteps
  include SharedAuthentication
  include SharedProject

  Then 'page should have graphs' do
    page.should have_selector ".stat-graph"
  end

  When 'I visit project "Shop" graph page' do
    project = Project.find_by_name("Shop")
    visit project_stat_graph_path(project, "master")
  end
end
