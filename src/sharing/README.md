# Sharing

This bounded context is concerned with managing sharing permissions and by extension, authorisation of different actions using Cedar policies.

## Cedar stuff

### resources

Fragment::<UUID>
Memory::<UUID>

### principals

User::<UUID>

### actions

create, update, read, delete

*all*
AllActions

*ReadAction*
readMemory
readFragment

*UpdateAction*
updateMemoryMetadata
updateFragmentContent

*DeleteAction*
deleteMemory
deleteFragment

*CreateAction*
createMemory
addFragment

addFragment - can add fragment to memory only when granted permissions or is the memory owner
readFragment - can read only when granted permissions or is the memory owner
updateFragmentContent - can update only when granted permissions or is the memory owner
deleteFragment - can delete only when granted permissions or is the memory owner
createMemory - can create only under own account
readMemory - can read only when granted permissions or is the memory owner
updateMemoryMetadata - can update only when granted permissions or is the memory owner
deleteMemory - can delete only if is the user that created the memory

### entities

User
Account
Fragment
Memory


### demo policies

#### when a memory is public, anyone can read it

permit(
    principal,
    action == Action::"read",
    resource == Memory::<UUID>
) when {
    resource.is_public
};

#### can do anything when owner

permit(
    principal,
    action == Action::"AllActions",
    resource == Memory::<UUID>
) when {
    principal == resource.created_by
};

#### addFragment

// can add fragment to memory when is the memory owner or has permissions
permit(
    principal == User::<UUID>,
    action == Action::"addFragment",
    resource == Memory::<UUID>
);

#### updateFragmentContent

// can update fragment content when is the memory owner or has permissions
permit(
    principal == User::<UUID>,
    action == Action::"updateFragmentContent",
    resource==Fragment::<UUID>
);

#### deleteFragment

permit(
    principal == User::<UUID>,
    action == Action::"deleteFragment",
    resource==Fragment::<UUID>
);
