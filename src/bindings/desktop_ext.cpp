// A nanobind wrapper of client.h

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/unordered_map.h>
#include <nanobind/stl/vector.h>

#include "desktop/desktop.h"
#include "desktop/frame.h"
#include "third_party/status/exceptions.h"

namespace nb = nanobind;

NB_MODULE(_core, m) {
  nb::module_::import_("numpy");

  nb::class_<Desktop>(m, "Desktop")
      .def_static("create", &Desktop::create, nb::arg("width"),
                  nb::arg("height"), nb::arg("visible") = false)
      .def("get_desktop_env", &Desktop::get_desktop_env)
      .def("key_press", &Desktop::key_press)
      .def("key_release", &Desktop::key_release)
      .def("move_mouse", &Desktop::move_mouse)
      .def("mouse_press", &Desktop::mouse_press)
      .def("mouse_release", &Desktop::mouse_release)
      .def("get_frame", [](Desktop& d) {
        Frame f = d.get_frame();

        uint8_t* data = f.take_pixels().release();
        nb::capsule owner(data, [](void* p) noexcept { free((uint8_t*)p); });

        return nb::ndarray<uint8_t, nb::numpy, nb::shape<-1, -1, 4>,
                           nb::c_contig>(
            data, {(uint32_t)f.width, (uint32_t)f.height, 4}, owner);
      });
}
