from .ScheduleContext import ScheduleContext
from orm.base import get_session

def dump_schedule_context(ctx: ScheduleContext):

    print("\n================ CONTEXT DUMP ================\n")

    # -------------------
    # CONFIG
    # -------------------
    print("CONFIG:")
    print(vars(ctx.CONFIG))
    print()

    # -------------------
    # ENTITIES
    # -------------------
    print("AUDIENCES:")
    for a in ctx.audiences:
        print(a)

    print("\nGROUPS:")
    for g in ctx.groups:
        print(g)

    print("\nPROFESSORS:")
    for p in ctx.professors:
        print(p)

    print("\nDISCIPLINES:")
    for d in ctx.disciplines:
        print(d)

    print("\nROOM TYPES:")
    for r in ctx.roomtypes:
        print(r)

    # -------------------
    # INDEXES
    # -------------------
    print("\nAUDIENCE BY ID:")
    print(ctx.audience_by_id)

    print("\nDISCIPLINE BY ID:")
    print(ctx.discipline_by_id)

    print("\nPROFESSOR BY ID:")
    print(ctx.professor_by_id)

    print("\nROOMTYPE BY ID:")
    print(ctx.roomtype_by_id)

    # -------------------
    # RELATIONS
    # -------------------
    print("\nPROFESSOR -> DISCIPLINES:")
    for k, v in ctx.professor_discipline.items():
        print(k, "->", v)

    print("\nDISCIPLINE -> PROFESSORS:")
    for k, v in ctx.discipline_professors.items():
        print(k, "->", v)

    print("\nAUDIENCE -> ROOMTYPES:")
    for k, v in ctx.audience_roomtypes.items():
        print(k, "->", v)

    print("\nROOMTYPE -> AUDIENCES:")
    for k, v in ctx.roomtype_audiences.items():
        print(k, "->", v)

    print("\n============== END DUMP ==============\n")

def main() -> None:
    with get_session() as session:
        ctx = ScheduleContext.load_from_db(session)
    dump_schedule_context(ctx)


if __name__ == "__main__":
    main()
