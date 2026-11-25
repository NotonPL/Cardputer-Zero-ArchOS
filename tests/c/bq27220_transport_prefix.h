/* SPDX-License-Identifier: GPL-2.0-only
 * Host-side test doubles. No Linux device nodes or real I2C access.
 */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
typedef uint8_t u8;
#define BQ27220 1
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define I2C_M_RD 1
#define I2C_SMBUS_BLOCK_MAX 32
struct i2c_client { void *adapter; unsigned short addr; };
struct i2c_msg { unsigned short addr, flags, len; u8 *buf; };
struct bq27xxx_device_info { void *dev, *bat; int chip; };
struct power_supply_battery_info { int unused; };
#define to_i2c_client(dev) ((struct i2c_client *)(dev))
static int transfers, programming_transfers, settings_calls, read_error;
static int i2c_transfer(void *adapter, struct i2c_msg *msg, int count)
{
    transfers++;
    if (count == 1) programming_transfers++;
    if (read_error) return read_error;
    if (count == 2) {
        assert(msg[0].flags == 0 && msg[0].len == 1);
        assert(msg[1].flags == I2C_M_RD);
        msg[1].buf[0] = 0x34;
        if (msg[1].len == 2) msg[1].buf[1] = 0x12;
    }
    return count;
}
static int i2c_smbus_read_i2c_block_data(struct i2c_client *c, u8 reg, int len, u8 *buf)
{ transfers++; memset(buf, 0x34, len); return read_error ? read_error : len; }
static void usleep_range(int low, int high) { }
static int get_unaligned_le16(u8 *data) { return data[0] | data[1] << 8; }
static void put_unaligned_le16(int value, u8 *data)
{ data[0] = value; data[1] = value >> 8; }
static int bq27220_battery_read_design_dt(struct bq27xxx_device_info *di, bool force, bool *found)
{ settings_calls++; *found = false; return 0; }
static int power_supply_get_battery_info(void *bat, struct power_supply_battery_info **info)
{ settings_calls++; *info = NULL; return 0; }
static int bq27220_battery_set_config(struct bq27xxx_device_info *di, struct power_supply_battery_info *info, bool force)
{ settings_calls++; return 0; }
static void power_supply_put_battery_info(void *bat, struct power_supply_battery_info *info)
{ settings_calls++; }
