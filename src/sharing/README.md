# Sharing

This bounded context is concerned with managing sharing permissions and by extension, authorisation of different actions using Cedar policies.

## Ubiquitous language
1. A memory has an owner.
2. A memory has a set of editors (other users) that is managed by the owner.
3. A memory has a set of readers (other users) that is managed by the owner.
4. A memory can be in two states: public or private.
5. If a memory is private, then the owner, and any user that is an editor can modify its fragments.
6. If a memory is private, then the owner and any user that is an editor or reader can read its fragments.
7. If a memory is public, anyone can read its fragments by navigating to its public url.
8. The url of public memories should be indexable by search engines.
9. Private memories should not be indexed by search engines.


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
