import logging
import json

ALL_SLOTS = ["T1A", "T1B", "T1C", "T1D"]

class CFSSlotHelper:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command(
            'CFS_PREPARE_SLOTS', self.cmd_prepare_slots,
            desc="Redirect empty CFS slots to loaded ones before print start")
        self.gcode.register_command(
            'CFS_DUMP', self.cmd_dump,
            desc="Dump CFS state for debugging")
        self.printer.register_event_handler('klippy:ready', self._handle_ready)
        self.box = None

    def _handle_ready(self):
        self.box = self.printer.lookup_object('box', None)
        if self.box is None:
            logging.warning("cfs_slot_helper: box module not found")

    def _probe_attr(self, gcmd, obj, obj_name, attr):
        try:
            val = getattr(obj, attr)
            gcmd.respond_info("CFS: %s.%s = %s" % (obj_name, attr, repr(val)[:300]))
        except AttributeError:
            pass
        except Exception as e:
            gcmd.respond_info("CFS: %s.%s err: %s" % (obj_name, attr, e))

    def cmd_dump(self, gcmd):
        if self.box is None:
            gcmd.respond_info("CFS_DUMP: box not available")
            return
        box_action = self.box.box_action
        box_state = self.box.box_state

        for tnn in ALL_SLOTS:
            try:
                avail = box_action.is_material_available(tnn)
                gcmd.respond_info("CFS: is_material_available(%s) = %s" % (tnn, avail))
            except Exception as e:
                gcmd.respond_info("CFS: is_material_available(%s) err: %s" % (tnn, e))

        try:
            m = box_state.get_Tnn_map()
            gcmd.respond_info("CFS: Tnn map = %s" % {k: v for k, v in m.items() if k in ALL_SLOTS})
        except Exception as e:
            gcmd.respond_info("CFS: get_Tnn_map err: %s" % e)

        self._probe_attr(gcmd, box_action, 'box_action', 'material_auto_refill_flag')

    def cmd_prepare_slots(self, gcmd):
        if self.box is None:
            gcmd.respond_info("CFS_PREPARE_SLOTS: box module not available, skipping")
            return

        box_action = self.box.box_action
        box_state = self.box.box_state

        loaded = []
        empty = []
        for tnn in ALL_SLOTS:
            try:
                if box_action.is_material_available(tnn):
                    loaded.append(tnn)
                else:
                    empty.append(tnn)
            except Exception:
                pass

        gcmd.respond_info("CFS: loaded=%s empty=%s" % (loaded, empty))

        if not loaded:
            gcmd.respond_info("CFS: no loaded slots found, skipping")
            return

        try:
            tnn_map = box_state.get_Tnn_map()
            changed = {}
            for tnn in empty:
                if tnn_map.get(tnn) != loaded[0]:
                    tnn_map[tnn] = loaded[0]
                    changed[tnn] = loaded[0]
            if changed:
                gcmd.respond_info("CFS: Tnn map updated: %s" % changed)
            else:
                gcmd.respond_info("CFS: Tnn map already correct")

            tnn_map2 = box_state.get_Tnn_map()
            gcmd.respond_info("CFS: Tnn map T1A→%s after update" % tnn_map2.get("T1A"))
        except Exception as e:
            gcmd.respond_info("CFS: Tnn map update err: %s" % e)

        try:
            box_action.material_auto_refill_flag = True
            gcmd.respond_info("CFS: material_auto_refill_flag = True")
        except Exception as e:
            gcmd.respond_info("CFS: flag err: %s" % e)

def load_config(config):
    return CFSSlotHelper(config)
