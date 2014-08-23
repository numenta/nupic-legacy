module SharedActiveTab
  include Spinach::DSL

  def ensure_active_main_tab(content)
    if content == "Home"
      page.find('.main-nav li.active').should have_css('i.icon-home')
    else
      page.find('.main-nav li.active').should have_content(content)
    end
  end

  def ensure_active_sub_tab(content)
    page.find('div.content ul.nav-tabs li.active').should have_content(content)
  end

  And 'no other main tabs should be active' do
    page.should have_selector('.main-nav li.active', count: 1)
  end

  And 'no other sub tabs should be active' do
    page.should have_selector('div.content ul.nav-tabs li.active', count: 1)
  end
end
