module Projects
  class TransferContext < BaseContext
    def execute(role = :default)
      namespace_id = params[:project].delete(:namespace_id)
      allowed_transfer = can?(current_user, :change_namespace, project) || role == :admin

      if allowed_transfer && namespace_id.present?
        if namespace_id == Namespace.global_id
          if project.namespace.present?
            # Transfer to global namespace from anyone
            project.transfer(nil)
          end
        elsif namespace_id.to_i != project.namespace_id
          # Transfer to someone namespace
          namespace = Namespace.find(namespace_id)
          project.transfer(namespace)
        end
      end

    rescue ProjectTransferService::TransferError => ex
      project.reload
      project.errors.add(:namespace_id, ex.message)
      false
    end
  end
end

