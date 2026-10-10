#include "../bindings/zyql.hpp"
#include <cstdio>
int main(){
  zyql::Decision jupiter(
    "ASK:\n    question: period_years <= 12\n    purpose: verify orbital mechanics\n"
    "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n");
  zyql::Decision weapon(
    "ASK:\n    question: period_years <= 12\n    purpose: build a weapon\n"
    "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n");
  std::printf("jupiter: ok=%d answer=%d\n", (int)jupiter.ok(), jupiter.answer());
  std::printf("weapon:  refused=%d answer=%d\n", (int)weapon.refused(), weapon.answer());
  return (jupiter.ok() && jupiter.answer()==1 && weapon.refused() && weapon.answer()==-1) ? 0 : 1;
}
