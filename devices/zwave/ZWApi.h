/*
 *      Copyright (C) 2008 Harald Klein <hari@vt100.at>
 *
 *      This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
 *      This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
 *      of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 *      See the GNU General Public License for more details.
 */

#define BASIC_TYPE_CONTROLLER                           0x01
#define BASIC_TYPE_STATIC_CONTROLLER                    0x02
#define BASIC_TYPE_SLAVE                                0x03
#define BASIC_TYPE_ROUTING_SLAVE                        0x04

#define GENERIC_TYPE_GENERIC_CONTROLLER                 0x01
#define GENERIC_TYPE_STATIC_CONTROLLER                  0x02
#define GENERIC_TYPE_AV_CONTROL_POINT                   0x03
#define GENERIC_TYPE_DISPLAY                            0x06
#define GENERIC_TYPE_GARAGE_DOOR                        0x07
#define GENERIC_TYPE_THERMOSTAT                         0x08
#define GENERIC_TYPE_WINDOW_COVERING                    0x09
#define GENERIC_TYPE_REPEATER_SLAVE                     0x0F
#define GENERIC_TYPE_SWITCH_BINARY                      0x10

#define GENERIC_TYPE_SWITCH_MULTILEVEL                  0x11
#define SPECIFIC_TYPE_NOT_USED				0x00
#define SPECIFIC_TYPE_POWER_SWITCH_MULTILEVEL		0x01
#define SPECIFIC_TYPE_MOTOR_MULTIPOSITION		0x03
#define SPECIFIC_TYPE_SCENE_SWITCH_MULTILEVEL		0x04
#define SPECIFIC_TYPE_CLASS_A_MOTOR_CONTROL		0x05
#define SPECIFIC_TYPE_CLASS_B_MOTOR_CONTROL		0x06
#define SPECIFIC_TYPE_CLASS_C_MOTOR_CONTROL		0x07

#define GENERIC_TYPE_SWITCH_REMOTE                      0x12
#define GENERIC_TYPE_SWITCH_TOGGLE                      0x13
#define GENERIC_TYPE_SENSOR_BINARY                      0x20
#define GENERIC_TYPE_SENSOR_MULTILEVEL                  0x21
#define GENERIC_TYPE_SENSOR_ALARM			0xa1
#define GENERIC_TYPE_WATER_CONTROL                      0x22
#define GENERIC_TYPE_METER_PULSE                        0x30
#define GENERIC_TYPE_ENTRY_CONTROL                      0x40
#define GENERIC_TYPE_SEMI_INTEROPERABLE                 0x50
#define GENERIC_TYPE_NON_INTEROPERABLE                  0xFF

#define SPECIFIC_TYPE_ADV_ZENSOR_NET_SMOKE_SENSOR	0x0a
#define SPECIFIC_TYPE_BASIC_ROUTING_SMOKE_SENSOR	0x06
#define SPECIFIC_TYPE_BASIC_ZENSOR_NET_SMOKE_SENSOR	0x08
#define SPECIFIC_TYPE_ROUTING_SMOKE_SENSOR		0x07
#define SPECIFIC_TYPE_ZENSOR_NET_SMOKE_SENSOR		0x09

