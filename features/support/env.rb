require 'simplecov' unless ENV['CI']

if ENV['TRAVIS']
  require 'coveralls'
  Coveralls.wear!
end

ENV['RAILS_ENV'] = 'test'
require './config/environment'

require 'rspec'
require 'database_cleaner'
require 'spinach/capybara'
require 'sidekiq/testing/inline'


%w(valid_commit select2_helper test_env).each do |f|
  require Rails.root.join('spec', 'support', f)
end

Dir["#{Rails.root}/features/steps/shared/*.rb"].each {|file| require file}

WebMock.allow_net_connect!
#
# JS driver
#
require 'capybara/poltergeist'
Capybara.javascript_driver = :poltergeist
Spinach.hooks.on_tag("javascript") do
  ::Capybara.current_driver = ::Capybara.javascript_driver
end
Capybara.default_wait_time = 10
Capybara.ignore_hidden_elements = false

DatabaseCleaner.strategy = :truncation

Spinach.hooks.before_scenario do
  TestEnv.init(mailer: false)

  DatabaseCleaner.start
end

Spinach.hooks.after_scenario do
  DatabaseCleaner.clean
end

Spinach.hooks.before_run do
  RSpec::Mocks::setup self

  include FactoryGirl::Syntax::Methods
end
