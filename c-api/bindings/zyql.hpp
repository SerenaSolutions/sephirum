// zyql.hpp — RAII wrapper for the ZYQL C API (C++11).
#ifndef ZYQL_HPP
#define ZYQL_HPP
#include <string>
#include "zyql.h"
namespace zyql {
class Decision {
    zyql_decision *d_;
public:
    explicit Decision(const std::string &program)
        : d_(zyql_decide(program.c_str())) {}
    ~Decision() { if (d_) zyql_close(d_); }
    Decision(const Decision&) = delete;
    Decision& operator=(const Decision&) = delete;
    bool ok()        const { return zyql_result(d_) == ZYQL_OK; }
    bool refused()   const { return zyql_result(d_) == ZYQL_REFUSED; }
    bool error()     const { return zyql_result(d_) == ZYQL_ERROR; }
    int  answer()    const { return zyql_answer(d_); }       // 1/0/-1
    const char* receipt() const { return zyql_receipt(d_); }  // certificate JSON
    const char* message() const { return zyql_message(d_); }
};
} // namespace zyql
#endif
