// Policy 0: A User can create a Memory in their Account and see what Memories are in their Account
permit (
    principal,  // User
    action in [Action::"CreateMemory", Action::"ListMemorySummaries"],
    resource is Account
) when {
    principal has "account" && principal.account == resource
};

// Policy 1: A User can perform any action on a Memory they own
permit (
  principal,  // User
  action,
  resource is Memory
)
when { resource.owner == principal };

// Policy 2: A User can see a Memory or Fragment if they are either a reader or editor
permit (
    principal,
    action in [Action::"GetMemory"],
    resource is Memory
)
when { principal in resource.readers || principal in resource.editors };

// Policy 3: A User can update a Memory if they are an editor
permit (
    principal,
    action in [Action::"SharedMemoryEditActions"],
    resource is Memory
)
when { principal in resource.editors };
