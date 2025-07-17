// complex_test.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_USERS 100
#define LOG(msg) printf("[LOG] %s:%d - %s\n", __FILE__, __LINE__, msg)

typedef struct {
    char name[50];
    int age;
    union {
        float gpa;
        int rank;
    } performance;
    enum { STUDENT, TEACHER } role;
} Person;

static const char *roles[] = { "Student", "Teacher" };

static void print_person(const Person *p) {
    printf("Name: %s\n", p->name);
    printf("Age: %d\n", p->age);
    printf("Role: %s\n", roles[p->role]);
    if (p->role == STUDENT)
        printf("GPA: %.2f\n", p->performance.gpa);
    else
        printf("Rank: %d\n", p->performance.rank);
}

int load_people(const char *filename, Person *people, int max) {
    FILE *fp = fopen(filename, "r");
    if (!fp) return -1;

    int count = 0;
    while (count < max && fscanf(fp, "%49[^,],%d,%f,%d\n",
           people[count].name,
           &people[count].age,
           &people[count].performance.gpa,
           (int*)&people[count].role) == 4) {
        count++;
    }
    fclose(fp);
    return count;
}

int main(void) {
    LOG("Program started");

    Person users[MAX_USERS];
    int count = load_people("people.txt", users, MAX_USERS);

    if (count < 0) {
        perror("Failed to load people");
        return 1;
    }

    for (int i = 0; i < count; i++) {
        print_person(&users[i]);
        printf("--------\n");
    }

    LOG("Program finished");
    return 0;
}
