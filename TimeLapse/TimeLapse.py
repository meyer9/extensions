# standard libraries
import contextlib
import functools
import gettext
import threading
import time

# third party libraries
# None

# local libraries
# None


_ = gettext.gettext


# This function will run on a thread. Consequently, it cannot modify the document model directly.
# Instead, when it needs to add data items to the containing data group, it will queue that operation
# to the main UI thread.
def perform_time_lapse(hardware_source, document_controller, data_group):
    with document_controller.create_task_context_manager(_("Time Lapse"), "table") as task:

        task.update_progress(_("Starting time lapse."), (0, 5))

        with contextlib.closing(hardware_source.create_view_task()) as hardware_source_task:

            task_data = {"headers": ["Number", "Time"]}

            for i in range(5):

                # update task results table. data should be in the form of
                # { "headers": ["Header1", "Header2"],
                #   "data": [["Data1A", "Data2A"], ["Data1B", "Data2B"], ["Data1C", "Data2C"]] }
                data = task_data.setdefault("data", list())
                task_data_entry = [str(i), time.strftime("%c", time.localtime())]
                data.append(task_data_entry)
                task.update_progress(_("Acquiring time lapse item {}.").format(i), (i + 1, 5), task_data)

                # Grab the next data item.
                data_and_metadata_list = hardware_source_task.grab_immediate()

                # Appending a data item to a group needs to happen on the UI thread.
                # This function will be placed in the document controllers UI thread queue.
                def append_data_item(_data_group, _data_and_metadata_list):
                    assert threading.current_thread().getName() == "MainThread"
                    for data_and_metadata in data_and_metadata_list:
                        data_item = document_controller.create_data_item_from_data_and_metadata(data_and_metadata, _("Time Lapse ") + str(i))
                        _data_group.add_data_item(data_item)

                document_controller.queue_task(functools.partial(append_data_item, data_group, data_and_metadata_list))

                # Go to sleep and wait for the next frame.
                time.sleep(1.0)

        task.update_progress(_("Finishing time lapse."), (5, 5))

        time.sleep(1.0)  # only here as a demonstration


class MenuItemDelegate(object):

    def __init__(self, api):
        self.__api = api
        self.menu_item_name = _("Time Lapse")  # menu item name
        self.menu_item_key_sequence = "Shift+Ctrl+T"

    def menu_item_execute(self, document_controller):
        data_group = document_controller.get_or_create_data_group(_("Time Lapse"))
        hardware_source = self.__api.get_hardware_source_by_id("random_capture", version="1.0")

        threading.Thread(target=perform_time_lapse, args=(hardware_source, document_controller, data_group)).start()


class TimeLapseExtension(object):

    # required for Swift to recognize this as an extension class.
    extension_id = "nion.swift.extensions.time_lapse"

    def __init__(self, api_broker):
        # grab the api object.
        api = api_broker.get_api(version="1", ui_version="1")
        # be sure to keep a reference or it will be closed immediately.
        self.__menu_item_ref = api.create_menu_item(MenuItemDelegate(api))

    def close(self):
        # close will be called when the extension is unloaded. in turn, close any references so they get closed. this
        # is not strictly necessary since the references will be deleted naturally when this object is deleted.
        self.__menu_item_ref.close()
        self.__menu_item_ref = None
