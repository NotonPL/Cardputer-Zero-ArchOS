/* SPDX-License-Identifier: GPL-2.0-only */
int main(void)
{
    struct i2c_client client = { .adapter = (void *)1, .addr = 0x55 };
    struct bq27xxx_device_info di = { .dev = &client, .chip = BQ27220 };
    u8 buf[32] = {0};
    for (int reg = 0; reg < 256; reg++) {
        assert(bq27xxx_battery_i2c_write(&di, reg, 0, true) == -EPERM);
        assert(bq27xxx_battery_i2c_write(&di, reg, 0xffff, false) == -EPERM);
        assert(bq27xxx_battery_i2c_bulk_write(&di, reg, buf, 32) == -EPERM);
    }
    assert(transfers == 0 && programming_transfers == 0);
    assert(bq27220_battery_settings(&di, false) == 0);
    assert(bq27220_battery_settings(&di, true) == -EPERM);
    assert(settings_calls == 0);
    assert(bq27xxx_battery_i2c_read(&di, 0x08, false) == 0x1234);
    assert(bq27xxx_battery_i2c_read(&di, 0x08, true) == 0x34);
    assert(bq27xxx_battery_i2c_bulk_read(&di, 0x08, buf, 2) == 0);
    assert(buf[0] == 0x34 && programming_transfers == 0);
    read_error = -EIO;
    assert(bq27xxx_battery_i2c_read(&di, 0x08, false) == -EIO);
    assert(bq27xxx_battery_i2c_bulk_read(&di, 0x08, buf, 2) == -EIO);
    read_error = 0;
    di.chip = 0; /* other bq27xxx chips retain original transport */
    assert(bq27xxx_battery_i2c_write(&di, 0, 1, false) == 0);
    assert(bq27xxx_battery_i2c_bulk_write(&di, 0, buf, 2) == 0);
    assert(programming_transfers == 2);
    puts("PASS: blocked 768 BQ27220 write calls; reads/errors and other-chip transport preserved");
    return 0;
}
