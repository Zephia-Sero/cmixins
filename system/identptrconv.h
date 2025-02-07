#ifndef IDENTPTRCONV_H
#define IDENTPTRCONV_H
#include <stddef.h>
#include <stdio.h>
#include <string.h>
static inline char *identptrconv(char *typeName)
{
	static char fixedName[1024];
	snprintf(fixedName, 1024, "%s", typeName);
	size_t indirectionLevel = 0;
	for (size_t i = 0; i < strlen(fixedName); ++i)
		if (fixedName[i] == '*')
			++indirectionLevel;
	if (indirectionLevel == 0)
		return fixedName;
	char *begin = fixedName;
	while (*begin != ' ' && *begin != '*')
		++begin;
	for (size_t i = 0; i < indirectionLevel; ++i)
		*(begin++) = 'p';
	*begin = '\0';
	return fixedName;
}
#endif
