#include <stdio.h>
#include <string.h>

#define MAX_DEVICES 10
#define COMPANY_NAME "EmbeddedSoft"

typedef enum {
    SENSOR,
    ACTUATOR,
    CONTROLLER
} DeviceType;

typedef struct {
    char name[50];
    int id;
    float firmware_version;
    DeviceType type;
} Device;

static const char *device_type_names[] = { "Sensor", "Actuator", "Controller" };

void print_device(const Device *d) {
    printf("Device Name : %s\n", d->name);
    printf("Device ID   : %d\n", d->id);
    printf("Firmware    : %.2f\n", d->firmware_version);
    printf("Type        : %s\n", device_type_names[d->type]);
}

float average_firmware(Device devices[], int count) {
    float total = 0;
    for (int i = 0; i < count; i++) {
        total += devices[i].firmware_version;
    }
    return (count > 0) ? (total / count) : 0;
}

int main() {
    Device devices[] = {
        { "TempSensor", 1, 1.05f, SENSOR },
        { "ServoActuator", 2, 2.10f, ACTUATOR },
        { "MainController", 3, 3.00f, CONTROLLER }
    };

    for (int i = 0; i < 3; i++) {
        print_device(&devices[i]);
        printf("---------------\n");
    }

    printf("Average Firmware Version: %.2f\n", average_firmware(devices, 3));
    return 0;
}
