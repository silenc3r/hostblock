TARGET := hostblock

ifeq ($(HOST_CACHE_DIR),)
	HOST_CACHE_DIR := /var/cache/hostblock
endif
ifeq ($(CONFIG_FILE),)
	CONFIG_FILE := /etc/hostblock.conf
endif

all: $(TARGET)

$(TARGET): hosts-generator.py
	cp $< $@
	sed -i -E 's#(HOST_CACHE_DIR = )None#\1"$(HOST_CACHE_DIR)"#' $@
	sed -i -E 's#(CONFIG_FILE = )None#\1"$(CONFIG_FILE)"#' $@

install: $(TARGET)
	install -d $(DESTDIR)/bin/
	install -m 755 $(TARGET) $(DESTDIR)/bin/
	install -d $(DESTDIR)$(HOST_CACHE_DIR)/
	install -d $(DESTDIR)/lib/systemd/system/
	install -m 644 hostblock-update.service $(DESTDIR)/lib/systemd/system/
	install -m 644 hostblock-update.timer $(DESTDIR)/lib/systemd/system/
	install -m 644 hostblock.conf $(DESTDIR)/etc/

uninstall:
	rm $(DESTDIR)/bin/$(TARGET)
	rm $(DESTDIR)/lib/systemd/system/hostblock-update.service
	rm $(DESTDIR)/lib/systemd/system/hostblock-update.timer

clean:
	rm $(TARGET)

.PHONY: all
