module Gitlab
  class Auth
    def find_for_ldap_auth(auth, signed_in_resource = nil)
      uid = auth.info.uid
      provider = auth.provider
      email = auth.info.email.downcase unless auth.info.email.nil?
      raise OmniAuth::Error, "LDAP accounts must provide an uid and email address" if uid.nil? or email.nil?

      if @user = User.find_by_extern_uid_and_provider(uid, provider)
        @user
      elsif @user = User.find_by_email(email)
        log.info "Updating legacy LDAP user #{email} with extern_uid => #{uid}"
        @user.update_attributes(extern_uid: uid, provider: provider)
        @user
      else
        create_from_omniauth(auth, true)
      end
    end

    def create_from_omniauth(auth, ldap = false)
      provider = auth.provider
      uid = auth.info.uid || auth.uid
      uid = uid.to_s.force_encoding("utf-8")
      name = auth.info.name.to_s.force_encoding("utf-8")
      email = auth.info.email.to_s.downcase unless auth.info.email.nil?

      ldap_prefix = ldap ? '(LDAP) ' : ''
      raise OmniAuth::Error, "#{ldap_prefix}#{provider} does not provide an email"\
        " address" if auth.info.email.blank?

      log.info "#{ldap_prefix}Creating user from #{provider} login"\
        " {uid => #{uid}, name => #{name}, email => #{email}}"
      password = Devise.friendly_token[0, 8].downcase
      @user = User.new({
        extern_uid: uid,
        provider: provider,
        name: name,
        username: email.match(/^[^@]*/)[0],
        email: email,
        password: password,
        password_confirmation: password,
      }, as: :admin).with_defaults
      @user.save!

      if Gitlab.config.omniauth['block_auto_created_users'] && !ldap
        @user.block
      end

      @user
    end

    def find_or_new_for_omniauth(auth)
      provider, uid = auth.provider, auth.uid
      email = auth.info.email.downcase unless auth.info.email.nil?

      if @user = User.find_by_provider_and_extern_uid(provider, uid)
        @user
      elsif @user = User.find_by_email(email)
        @user.update_attributes(extern_uid: uid, provider: provider)
        @user
      else
        if Gitlab.config.omniauth['allow_single_sign_on']
          @user = create_from_omniauth(auth)
          @user
        end
      end
    end

    def log
      Gitlab::AppLogger
    end

    def ldap_auth(login, password)
      # Check user against LDAP backend if user is not authenticated
      # Only check with valid login and password to prevent anonymous bind results
      return nil unless ldap_conf.enabled && !login.blank? && !password.blank?

      ldap = OmniAuth::LDAP::Adaptor.new(ldap_conf)
      ldap_user = ldap.bind_as(
        filter: Net::LDAP::Filter.eq(ldap.uid, login),
        size: 1,
        password: password
      )

      User.find_by_extern_uid_and_provider(ldap_user.dn, 'ldap') if ldap_user
    end

    def ldap_conf
      @ldap_conf ||= Gitlab.config.ldap
    end
  end
end
