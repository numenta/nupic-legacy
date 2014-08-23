xml.instruct!
xml.feed "xmlns" => "http://www.w3.org/2005/Atom", "xmlns:media" => "http://search.yahoo.com/mrss/" do
  xml.title   "Dashboard feed#{" - #{current_user.name}" if current_user.name.present?}"
  xml.link    :href => dashboard_url(:atom), :rel => "self", :type => "application/atom+xml"
  xml.link    :href => dashboard_url, :rel => "alternate", :type => "text/html"
  xml.id      projects_url
  xml.updated @events.maximum(:updated_at).strftime("%Y-%m-%dT%H:%M:%SZ") if @events.any?

  @events.each do |event|
    if event.proper?
      xml.entry do
        event_link = event_feed_url(event)
        event_title = event_feed_title(event)
        event_summary = event_feed_summary(event)

        xml.id      "tag:#{request.host},#{event.created_at.strftime("%Y-%m-%d")}:#{event.id}"
        xml.link    :href => event_link
        xml.title   truncate(event_title, :length => 80)
        xml.updated event.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        xml.media   :thumbnail, :width => "40", :height => "40", :url => gravatar_icon(event.author_email)
        xml.author do |author|
          xml.name event.author_name
          xml.email event.author_email
        end
        xml.summary(:type => "xhtml") { |x| x << event_summary unless event_summary.nil? }
      end
    end
  end
end
