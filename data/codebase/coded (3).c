
// coded.c - Complex C example for RAG testing

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_USERS 100
#define APP_NAME "CodedApp"

typedef enum {
    ROLE_ADMIN,
    ROLE_USER,
    ROLE_GUEST
} UserRole;

typedef struct {
    int id;
    char name[50];
    UserRole role;
} User;

static User user_db[MAX_USERS];
static int user_count = 0;

// Initialize the user database
void init_users() {
    user_count = 3;
    user_db[0] = (User){1, "Alice", ROLE_ADMIN};
    user_db[1] = (User){2, "Bob", ROLE_USER};
    user_db[2] = (User){3, "Charlie", ROLE_GUEST};
}

// Find a user by name
User *find_user(const char *name) {
    for (int i = 0; i < user_count; i++) {
        if (strcmp(user_db[i].name, name) == 0)
            return &user_db[i];
    }
    return NULL;
}

// Promote a user to admin
int promote_user(const char *name) {
    User *u = find_user(name);
    if (u && u->role != ROLE_ADMIN) {
        u->role = ROLE_ADMIN;
        return 1;
    }
    return 0;
}

// Print all users
void list_users() {
    printf("User List:\n");
    for (int i = 0; i < user_count; i++) {
        printf("%d: %s (%d)\n", user_db[i].id, user_db[i].name, user_db[i].role);
    }
}

// Entry point
int main() {
    init_users();
    list_users();
    promote_user("Bob");
    printf("\nAfter Promotion:\n");
    list_users();
    return 0;
}
